import { homeworkTools } from './homeworkTools.js';
import { weeklyPlanTools } from './weeklyPlanTools.js';

export const getAllTools = () => {
  return [
    ...homeworkTools,
    ...weeklyPlanTools,
  ];
};
