// Define weekly plan-related tool definitions
export const weeklyPlanTools = [
  {
    name: "get_schedule_for_date",
    description: "Retrieves the class schedule for a specific date. Use this when the user asks what classes they have on a particular day, what to bring to school, or what subjects are scheduled.",
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
    description: "Retrieves schedule entries for a specific subject on a given date. Use this when the user asks about a specific class/subject for a day (e.g., 'do I have math tomorrow?', 'what do I have in English class tomorrow?').",
    input_schema: {
      type: "object",
      properties: {
        subject: {
          type: "string",
          description: "The name of the subject (e.g., 'Math', 'English', 'Science')"
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
    description: "Retrieves the class schedule for a date range. Use this for weekly schedule queries or multi-day planning.",
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
    description: "Retrieves information about what materials/items to bring to school for a specific date. Returns schedule with descriptions and homework requirements. Use this when the user asks 'what should I bring tomorrow?' or 'what do I need for school?'.",
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
