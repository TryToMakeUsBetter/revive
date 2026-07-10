import React from 'react';

interface Props {
  url: string;
}

const ChartDisplay: React.FC<Props> = ({ url }) => {
  return (
    <div className="chart-display">
      <img src={url} alt="图表" />
      <div className="chart-caption">📊 {url}</div>
    </div>
  );
};

export default ChartDisplay;
