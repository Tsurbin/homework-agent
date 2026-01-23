// Define weekly plan-related tool definitions
export const weeklyPlanTools = [
  {
    name: "get_schedule_for_date",
    description: "Retrieves the class schedule for a specific date including class comments which contain homework assignments, what to bring (workbooks, materials), and lesson topics. Use this when the user asks what classes they have, what homework was assigned, what workbooks/materials to bring, or what subjects are scheduled for a specific day.",
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
    name: "get_schedule_for_subject",
    description: "Retrieves schedule entries for a specific subject on a given date, including class comments with homework details, workbook pages, and materials to bring. Use this when the user asks about homework, assignments, or what to bring for a specific subject/class on a particular day (e.g., 'what homework do I have in math?', 'what pages in science?', 'what workbook for English?').",
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
    name: "get_schedule_by_date_range",
    description: "Retrieves the class schedule for a date range including all class comments with homework and materials. Use this for weekly schedule queries or multi-day planning.",
    input_schema: {
      type: "object",
      properties: {
        start_date: {
          type: "string",
          description: "Start date in YYYY-MM-DD format"
        },
        end_date: {
          type: "string",
          description: "End date in YYYY-MM-DD format"
        }
      },
      required: ["start_date", "end_date"]
    }
  },
  {
    name: "get_what_to_bring",
    description: "Retrieves detailed information about what materials, workbooks (חוברות), and items to bring to school for a specific date. The class_comments field contains homework assignments, workbook names and page numbers. Use this when the user asks 'what should I bring?', 'what workbook?', 'which pages?', 'what homework?' for a specific date.",
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
  }
];

export default weeklyPlanTools;
