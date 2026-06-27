import React, { useRef, useEffect } from 'react';

export interface PlanetNode {
  id: string;
  x: number;
  y: number;
  radius_km: number;
  active_towers: number;
  status?: 'online' | 'offline'; // Added for UI tracking
}

interface UniverseCanvasProps {
  nodes: PlanetNode[];
  pathTaken: string[];
  onPlanetClick: (nodeId: string) => void;
}

export const UniverseCanvas: React.FC<UniverseCanvasProps> = ({ nodes, pathTaken, onPlanetClick }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Responsive canvas size
    const resizeCanvas = () => {
      const parent = canvas.parentElement;
      if (parent) {
        canvas.width = parent.clientWidth;
        canvas.height = parent.clientHeight;
        draw(ctx);
      }
    };

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    return () => window.removeEventListener('resize', resizeCanvas);
  }, [nodes, pathTaken]);

  const calculateTransform = (canvasW: number, canvasH: number, nodes: PlanetNode[]) => {
    if (nodes.length === 0) return { dynamicScale: 1, centerX: 0, centerY: 0 };
    const minX = Math.min(...nodes.map(n => n.x));
    const maxX = Math.max(...nodes.map(n => n.x));
    const minY = Math.min(...nodes.map(n => n.y));
    const maxY = Math.max(...nodes.map(n => n.y));
    
    const rangeX = maxX - minX || 1;
    const rangeY = maxY - minY || 1;
    const padding = 80;
    const scaleX = Math.max((canvasW - padding * 2) / rangeX, 0.1);
    const scaleY = Math.max((canvasH - padding * 2) / rangeY, 0.1);
    const dynamicScale = Math.min(scaleX, scaleY, 1.2);

    return { dynamicScale, centerX: (minX + maxX) / 2, centerY: (minY + maxY) / 2 };
  };

  const getCoords = (n: PlanetNode, canvasW: number, canvasH: number, transform: any) => {
    return {
      x: canvasW / 2 + (n.x - transform.centerX) * transform.dynamicScale,
      y: canvasH / 2 + (n.y - transform.centerY) * transform.dynamicScale
    };
  };

  const draw = (ctx: CanvasRenderingContext2D) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const transform = calculateTransform(canvas.width, canvas.height, nodes);

    // Draw active routing path
    if (pathTaken && pathTaken.length > 1) {
      ctx.beginPath();
      for (let i = 0; i < pathTaken.length; i++) {
        const nodeId = pathTaken[i];
        const node = nodes.find(n => n.id === nodeId);
        if (node) {
          const { x, y } = getCoords(node, canvas.width, canvas.height, transform);
          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
      }
      ctx.strokeStyle = '#000000'; // Pure Black
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Draw planets
    nodes.forEach(node => {
      const { x, y } = getCoords(node, canvas.width, canvas.height, transform);
      const visualRadius = Math.max(15, node.radius_km / 1500); // Scale down radius for UI

      // Draw planet core
      ctx.beginPath();
      ctx.arc(x, y, visualRadius, 0, Math.PI * 2);
      ctx.fillStyle = node.status === 'offline' ? '#F0F0F0' : '#FFFFFF'; // Light gray or white core
      ctx.strokeStyle = node.status === 'offline' ? '#CCCCCC' : '#000000'; // Light gray if offline, black if online
      ctx.lineWidth = 2;
      if (node.status === 'offline') {
         ctx.setLineDash([4, 4]); // Dashed line for offline planets
      } else {
         ctx.setLineDash([]);
      }
      ctx.fill();
      ctx.stroke();
      ctx.setLineDash([]); // Reset line dash for other drawings

      // Draw towers around planet
      const towers = node.active_towers;
      for (let i = 0; i < towers; i++) {
        const angle = (i * (Math.PI * 2)) / towers;
        const tx = x + (visualRadius + 8) * Math.cos(angle);
        const ty = y + (visualRadius + 8) * Math.sin(angle);
        
        ctx.beginPath();
        ctx.arc(tx, ty, 2, 0, Math.PI * 2);
        ctx.fillStyle = node.status === 'offline' ? '#CCCCCC' : '#000000';
        ctx.fill();
      }

      // Draw label
      ctx.fillStyle = '#000000';
      ctx.font = '14px Inter';
      ctx.textAlign = 'center';
      ctx.fillText(node.id.toUpperCase(), x, y - visualRadius - 20);
    });
  };

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    
    const transform = calculateTransform(canvas.width, canvas.height, nodes);

    for (const node of nodes) {
      const { x: nx, y: ny } = getCoords(node, canvas.width, canvas.height, transform);
      const visualRadius = Math.max(15, node.radius_km / 1500);

      // Check distance from click to planet center
      const dist = Math.sqrt((clickX - nx) ** 2 + (clickY - ny) ** 2);
      if (dist <= visualRadius + 10) {
        onPlanetClick(node.id);
        break;
      }
    }
  };

  // Re-draw when nodes update
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (ctx && canvas) {
      draw(ctx);
    }
  }, [nodes, pathTaken]);

  return (
    <canvas 
      ref={canvasRef} 
      onClick={handleClick}
      style={{ display: 'block' }}
    />
  );
};
