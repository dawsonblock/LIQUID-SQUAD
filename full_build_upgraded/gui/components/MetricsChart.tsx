import React, { useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface MetricsChartProps {
  title: string;
  type: 'line' | 'bar' | 'doughnut';
  data: any;
  options?: any;
}

export default function MetricsChart({ title, type, data, options = {} }: MetricsChartProps) {
  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          color: 'rgb(107, 114, 128)', // gray-500
        },
      },
      title: {
        display: true,
        text: title,
        color: 'rgb(55, 65, 81)', // gray-700
        font: {
          size: 16,
          weight: 'bold',
        },
        padding: {
          bottom: 20,
        },
      },
    },
    scales: type !== 'doughnut' ? {
      x: {
        grid: {
          color: 'rgb(229, 231, 235)', // gray-200
        },
        ticks: {
          color: 'rgb(107, 114, 128)', // gray-500
        },
      },
      y: {
        grid: {
          color: 'rgb(229, 231, 235)', // gray-200
        },
        ticks: {
          color: 'rgb(107, 114, 128)', // gray-500
        },
      },
    } : undefined,
    ...options,
  };

  const ChartComponent = {
    line: Line,
    bar: Bar,
    doughnut: Doughnut,
  }[type];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="h-80">
        <ChartComponent data={data} options={defaultOptions} />
      </div>
    </div>
  );
}