import React from 'react';
import styles from './StatusIndicator.module.css';

interface StatusIndicatorProps {
  status: string;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status }) => {
  const isThinking = status.toLowerCase().includes('thinking');
  const isTyping = status.toLowerCase().includes('typing');
  const isError = status.toLowerCase().includes('error');
  
  console.log('StatusIndicator - status:', status, 'isTyping:', isTyping, 'isThinking:', isThinking);
  
  return (
    <div className={`${styles.statusIndicator} ${isThinking ? styles.thinking : ''} ${isTyping ? styles.typing : ''} ${isError ? styles.error : ''}`}>
      <div className={styles.statusDot}></div>
      <span className={styles.statusText}>{status}</span>
    </div>
  );
};

export default StatusIndicator;
