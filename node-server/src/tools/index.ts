import { homeworkTools } from './homeworkTools';

export const getAllTools = () => {
  return [
    ...homeworkTools,
    // ...scheduleTools, // Future
  ];
};

