// Define homework-related tool definitions
export const homeworkTools = [
  {
    name: "get_homework_by_date",
    description: "Retrieves detailed homework tasks and assignments for a specific subject and date. Returns homework_text field which contains workbook names, page numbers, and specific tasks. Use this when the user asks about homework details, workbook pages, or assignments for a specific subject.",
    input_schema: {
      type: "object",
      properties: {
        subject: {
          type: "string",
          description: "The name of the subject in Hebrew (e.g., 'מתמטיקה', 'מדע וטכנולוגיה', 'שפה', 'אנגלית')"
        },
        date: {
          type: "string",
          description: "The date in YYYY-MM-DD format"
        }
      },
      required: ["subject", "date"]
    }
  },
  {
    name: "get_homework_by_date_range",
    description: "Retrieves all homework tasks for a subject within a date range. Returns homework_text with workbook pages and assignments. Use this for weekly or multi-day homework queries.",
    input_schema: {
      type: "object",
      properties: {
        subject: {
          type: "string",
          description: "The name of the subject in Hebrew (e.g., 'מתמטיקה', 'מדע וטכנולוגיה', 'שפה')"
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
      required: ["subject", "start_date", "end_date"]
    }
  },
  {
    name: "get_all_homework_for_date",
    description: "Retrieves homework tasks for ALL subjects on a specific date. Returns homework_text containing workbook names, page numbers and assignments. Use this when the user asks 'what's my homework today' without specifying a subject.",
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
    description: "Retrieves all upcoming homework tasks from today onwards, optionally filtered by subject. Returns homework_text with detailed assignments.",
    input_schema: {
      type: "object",
      properties: {
        subject: {
          type: "string",
          description: "Optional: filter by specific subject name in Hebrew"
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