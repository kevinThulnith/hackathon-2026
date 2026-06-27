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

const SCALE = 1.2;
const OFFSET_X = 150;
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

  const draw = (ctx: CanvasRenderingContext2D) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Center the map a bit based on canvas size
    const cx = canvas.width / 2 - 250;
    const cy = canvas.height / 2;

    const getCoords = (n: PlanetNode) => {
      return {
        x: cx + (n.x * SCALE) + OFFSET_X,
        y: cy + (n.y * SCALE)
      };
    };

    // Draw active routing path
    if (pathTaken && pathTaken.length > 1) {
      ctx.beginPath();
      for (let i = 0; i < pathTaken.length; i++) {
        const nodeId = pathTaken[i];
        const node = nodes.find(n => n.id === nodeId);
        if (node) {
          const { x, y } = getCoords(node);
          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
      }
      ctx.strokeStyle = '#00f0ff';
      ctx.lineWidth = 4;
      ctx.shadowBlur = 15;
      ctx.shadowColor = '#00f0ff';
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    // Draw planets
    nodes.forEach(node => {
      const { x, y } = getCoords(node);
      const visualRadius = Math.max(15, node.radius_km / 1500); // Scale down radius for UI

      // Draw glow
      ctx.beginPath();
      ctx.arc(x, y, visualRadius + 10, 0, Math.PI * 2);
      ctx.fillStyle = node.status === 'offline' ? 'rgba(255, 0, 85, 0.2)' : 'rgba(0, 240, 255, 0.15)';
      ctx.fill();

      // Draw planet core
      ctx.beginPath();
      ctx.arc(x, y, visualRadius, 0, Math.PI * 2);
      ctx.fillStyle = node.status === 'offline' ? '#ff0055' : '#0b192c';
      ctx.strokeStyle = node.status === 'offline' ? '#cc0044' : '#00f0ff';
      ctx.lineWidth = 2;
      ctx.fill();
      ctx.stroke();

      // Draw towers around planet
      const towers = node.active_towers;
      for (let i = 0; i < towers; i++) {
        const angle = (i * (Math.PI * 2)) / towers;
        const tx = x + (visualRadius + 5) * Math.cos(angle);
        const ty = y + (visualRadius + 5) * Math.sin(angle);
        
        ctx.beginPath();
        ctx.arc(tx, ty, 2, 0, Math.PI * 2);
        ctx.fillStyle = node.status === 'offline' ? '#330011' : '#ffffff';
        ctx.fill();
      }

      // Draw label
      ctx.fillStyle = '#ffffff';
      ctx.font = '14px Inter';
      ctx.textAlign = 'center';
      ctx.fillText(node.id, x, y - visualRadius - 15);
    });
  };

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    const cx = canvas.width / 2 - 250;
    const cy = canvas.height / 2;

    for (const node of nodes) {
      const nx = cx + (node.x * SCALE) + OFFSET_X;
      const ny = cy + (node.y * SCALE);
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
