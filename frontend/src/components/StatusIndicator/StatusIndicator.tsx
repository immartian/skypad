import React from 'react';
import styles from './StatusIndicator.module.css';

interface StatusIndicatorProps {
  status: string;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status }) => {
  return (
    <div className={styles.statusIndicator}>
      Status: <span className={styles.statusText}>{status}</span>
    </div>
  );
};

export default StatusIndicator;
