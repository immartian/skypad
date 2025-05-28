import React from 'react';
import styles from './StatusIndicator.module.css';

interface StatusIndicatorProps {
  status: string;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status }) => {
  const isThinking = status.toLowerCase().includes('thinking');
  const isError = status.toLowerCase().includes('error');
  
  return (
    <div className={`${styles.statusIndicator} ${isThinking ? styles.thinking : ''} ${isError ? styles.error : ''}`}>
      <div className={styles.statusDot}></div>
      <span className={styles.statusText}>{status}</span>
    </div>
  );
};

export default StatusIndicator;
