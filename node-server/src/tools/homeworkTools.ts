// Define homework-related tool definitions
export const homeworkTools = [
  {
    name: "get_homework_by_date",
    description: "Retrieves homework tasks for a specific class and date. Use this when the user asks about homework for a particular day.",
    input_schema: {
      type: "object",
      properties: {
        class_name: {
          type: "string",
          description: "The name of the class (e.g., 'Math', 'English', 'Science')"
        },
        date: {
          type: "string",
          description: "The date in YYYY-MM-DD format"
        }
      },
      required: ["class_name", "date"]
    }
  },
  {
    name: "get_homework_by_date_range",
    description: "Retrieves all homework tasks for a class within a date range. Use this for weekly or multi-day homework queries.",
    input_schema: {
      type: "object",
      properties: {
        class_name: {
          type: "string",
          description: "The name of the class"
        },
        start_date: {
          type: "string",
          description: "Start date in YYYY-MM-DD format"
        },
        end_date: {
          type: "string",
          description: "End date in YYYY-MM-DD format"
        }
      },
      required: ["class_name", "start_date", "end_date"]
    }
  },
  {
    name: "get_all_homework_for_date",
    description: "Retrieves homework tasks for ALL classes on a specific date. Use this when the user asks 'what's my homework today' without specifying a class.",
    input_schema: {
      type: "object",
      properties: {
        date: {
          type: "string",
          description: "The date in YYYY-MM-DD format"
        }
      },
      required: ["date"]
    }
  },
  {
    name: "get_upcoming_homework",
    description: "Retrieves all upcoming homework tasks from today onwards, optionally filtered by class.",
    input_schema: {
      type: "object",
      properties: {
        class_name: {
          type: "string",
          description: "Optional: filter by specific class name"
        },
        limit: {
          type: "number",
          description: "Maximum number of tasks to return (default: 10)"
        }
      },
      required: []
    }
  }
];

export default homeworkTools;