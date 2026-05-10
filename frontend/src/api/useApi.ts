import { useContext } from 'react';
import { ApiContext, type ApiContextValue } from './ApiContext';

export const useApi = (): ApiContextValue => {
  const context = useContext(ApiContext);
  if (!context) throw new Error('useApi must be used within an ApiProvider');
  return context;
};