import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .services import RelicUniverse, CodexTranslator, UnknownNodeError, NodeOfflineError

# Initialize our universe as a global singleton so memory persists for the Chaos Test
universe = RelicUniverse()


def get_universe(request):
    "Milestone 1: Universe Initialization - Return all nodes"
    return JsonResponse({"nodes": universe.nodes})


def _parse_json_body(request):
    """
    Returns (data, error_response). error_response is None on success.
    Centralizes malformed-JSON handling so every POST endpoint returns
    a clean 400 instead of an uncaught json.JSONDecodeError -> 500.
    """
    if not request.body:
        return None, JsonResponse({"error": "Request body is empty"}, status=400)
    try:
        return json.loads(request.body), None
    except json.JSONDecodeError:
        return None, JsonResponse(
            {"error": "Request body is not valid JSON"}, status=400
        )


@csrf_exempt
@require_http_methods(["POST"])
def route_packet(request):
    "Milestone 2 & 3: Multi-Hop Proof and Latency Breakdown"
    data, err = _parse_json_body(request)
    if err:
        return err

    origin = data.get("origin")
    destination = data.get("destination")
    payload = data.get("payload", "Hello world")

    if not origin or not destination:
        return JsonResponse(
            {"error": "Both 'origin' and 'destination' are required"}, status=400
        )

    # 1. Get the shortest path. UnknownNodeError -> 404 (the node_id
    # itself is invalid). This is the case that used to come back as
    # either a generic 500 (KeyError) or a misleading "undeliverable" 400.
    try:
        path_nodes = universe.find_shortest_path(origin, destination)
    except UnknownNodeError as e:
        return JsonResponse(
            {
                "error": str(e),
                "field": "origin" if e.node_id == origin else "destination",
            },
            status=404,
        )

    if not path_nodes:
        # Genuinely no route: every path is blocked by dead nodes or
        # exceeds max void hop distance. This 400 now ONLY means that.
        return JsonResponse(
            {"error": f"Route from {origin} to {destination} undeliverable"},
            status=400,
        )

    hop_log = []
    total_latency_seconds = 0.0

    # 2. Build the precise packet trace and latency breakdown
    for i in range(len(path_nodes) - 1):
        current_id = path_nodes[i]
        next_id = path_nodes[i + 1]

        t_exit, t_entry = universe.find_line_of_sight_towers(current_id, next_id)
        L = universe.calculate_void_distance(current_id, next_id)

        Tp = universe.calculate_crust_transit_time(
            universe.nodes[current_id], 0, t_exit
        )  # Assuming entry at tower 0 for simplicity on origin
        Tv = universe.calculate_void_latency(
            universe.nodes[current_id], universe.nodes[next_id], L
        )

        hop_latency = Tp + Tv
        total_latency_seconds += hop_latency

        next_codex = universe.nodes[next_id]["codex"]
        encoded_payload = CodexTranslator.encode_payload(payload, next_codex)

        hop_log.append(
            {
                "hop_number": i + 1,
                "from_planet": current_id,
                "to_planet": next_id,
                "tower_routing": f"Exit Tower {t_exit} -> Entry Tower {t_entry}",
                "void_distance_km": round(L, 2),
                "latency_breakdown": {
                    "internal_crust_time_sec": round(Tp, 6),
                    "void_travel_time_sec": round(Tv, 6),
                    "total_hop_latency_sec": round(hop_latency, 6),
                },
                "data_translation": {
                    "next_hop_codex": next_codex,
                    "binary_transmission_stream": encoded_payload,
                },
            }
        )

    # 3. Final Mandatory Packet Schema
    packet_schema = {
        "origin_id": path_nodes[0],
        "destination_id": path_nodes[-1],
        "current_id": path_nodes[-1],  # Packet has arrived
        "payload": payload,  # Re-decoded at final destination
        "total_latency_seconds": round(total_latency_seconds, 6),
        "path_taken": path_nodes,
        "hop_log": hop_log,
    }

    return JsonResponse(packet_schema)


@csrf_exempt
@require_http_methods(["POST"])
def toggle_node(request):
    "Milestone 4: Chaos Test - Kill or revive a node dynamically"
    data, err = _parse_json_body(request)
    if err:
        return err

    node_id = data.get("node_id")
    action = data.get("action", "kill")  # 'kill' or 'revive'

    if not node_id:
        return JsonResponse({"error": "'node_id' is required"}, status=400)

    if action not in ("kill", "revive"):
        return JsonResponse(
            {"error": f"Invalid action '{action}', must be 'kill' or 'revive'"},
            status=400,
        )

    try:
        if action == "kill":
            canonical = universe.kill_node(node_id)
            return JsonResponse({"status": f"{canonical} offline!"})
        else:
            canonical = universe.revive_node(node_id)
            return JsonResponse({"status": f"{canonical} back online!"})
    except UnknownNodeError as e:
        return JsonResponse({"error": str(e)}, status=404)


def HealthCheckView(request):
    "Health Check Endpoint"
    return JsonResponse({"status": "healthy"})
