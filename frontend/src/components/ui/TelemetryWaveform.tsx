import React, { useMemo } from 'react';

interface TelemetryWaveformProps {
  seed: number;
  colorClass: 'amber' | 'green' | 'red';
  width?: number;
  height?: number;
}

const colorMap = {
  amber: '#ff9100',
  green: '#00ff66',
  red: '#ff3333',
};

/**
 * TelemetryWaveform - Generates a mathematical SVG waveform visualization
 * with seeded randomness for deterministic wave patterns.
 * 
 * @param seed - Numeric seed for deterministic waveform generation
 * @param colorClass - Color variant ('amber', 'green', 'red')
 * @param width - SVG width in pixels (default: 120)
 * @param height - SVG height in pixels (default: 30)
 */
export default function TelemetryWaveform({
  seed,
  colorClass,
  width = 120,
  height = 30,
}: TelemetryWaveformProps) {
  const color = colorMap[colorClass];

  // Seeded random number generator for deterministic output
  const seededRandom = (x: number): number => {
    const s = Math.sin(x * 12.9898 + seed * 78.233) * 43758.5453;
    return s - Math.floor(s);
  };

  // Generate SVG path points using mathematical oscillation
  const points = useMemo(() => {
    const pointCount = 60;
    const yCenter = height / 2;
    const amplitude = height * 0.35;

    let pathData = `M 0 ${yCenter}`;

    for (let i = 0; i <= pointCount; i++) {
      const x = (i / pointCount) * width;
      // Combine multiple sine waves with seeded randomness
      const waveA = Math.sin((i / pointCount) * Math.PI * 2) * amplitude;
      const waveB = Math.sin((i / pointCount) * Math.PI * 4) * amplitude * 0.5;
      const noise = (seededRandom(i) - 0.5) * amplitude * 0.3;
      const y = yCenter + waveA + waveB + noise;

      pathData += ` L ${x} ${y}`;
    }

    return pathData;
  }, [seed, width, height]);

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="inline-block"
      style={{ strokeLinecap: 'round', strokeLinejoin: 'round' }}
    >
      <path
        d={points}
        stroke={color}
        strokeWidth="1.5"
        fill="none"
        opacity="0.85"
      />
      {/* Glow effect */}
      <path
        d={points}
        stroke={color}
        strokeWidth="3"
        fill="none"
        opacity="0.15"
        filter="blur(1px)"
      />
    </svg>
  );
}
