import { homeworkTools } from './homeworkTools.js';

export const getAllTools = () => {
  return [
    ...homeworkTools,
    // ...scheduleTools, // Future
  ];
};

