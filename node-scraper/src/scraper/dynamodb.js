import AWS from 'aws-sdk';

/**
 * Homework item data structure - optimized for DynamoDB
 */
class HomeworkItem {
    constructor({
        date,
        subject,
        description,
        hour = null,
        dueDate = null,
        homeworkText = null,
        teacher = null,
        classDescription = null,
        createdAt = new Date().toISOString()
    }) {
        this.date = date; // YYYY-MM-DD (will be part of composite key)
        this.subject = subject; // Subject name
        this.description = description; // Homework description
        this.hour = hour; // The lesson hour (שעה) - e.g., "שיעור 1", "שיעור 2"
        this.dueDate = dueDate; // YYYY-MM-DD
        this.homeworkText = homeworkText; // The actual homework assignment text
        this.teacher = teacher; // Teacher name
        this.classDescription = classDescription; // Class description
        this.createdAt = createdAt;
    }

    /**
     * Generate composite key for DynamoDB: date#hour#subject
     */
    get compositeKey() {
        const hourPart = this.hour || "unknown";
        return `${this.date}#${hourPart}#${this.subject}`;
    }

    /**
     * Generate hour_subject sort key
     */
    get hourSubjectKey() {
        const hourPart = this.hour || "unknown";
        return `${hourPart}#${this.subject}`;
    }
}

/**
 * DynamoDB handler for homework items.
 * 
 * Table structure:
 * - Partition Key (PK): date (YYYY-MM-DD)
 * - Sort Key (SK): hour#subject (e.g., "שיעור 1#מתמטיקה")
 * - Attributes: description, due_date, homework_text, created_at, updated_at
 */
class DynamoDBHandler {
    constructor(tableName, regionName = process.env.AWS_REGION || 'us-east-1') {
        this.tableName = tableName;
        this.regionName = regionName;

        // Configure AWS
        AWS.config.update({ region: this.regionName });
        
        // Initialize DynamoDB client
        this.dynamodb = new AWS.DynamoDB();
        this.docClient = new AWS.DynamoDB.DocumentClient();

        console.log(`Initialized DynamoDB handler for table: ${tableName}`);
    }

    /**
     * Create the DynamoDB table if it doesn't exist.
     * 
     * @returns {Promise<boolean>} True if table was created, False if it already existed
     */
    async createTableIfNotExists() {
        try {
            // Check if table exists
            await this.dynamodb.describeTable({ TableName: this.tableName }).promise();
            console.log(`Table ${this.tableName} already exists`);
            return false;

        } catch (error) {
            if (error.code === 'ResourceNotFoundException') {
                // Table doesn't exist, create it
                console.log(`Creating table ${this.tableName}`);

                const params = {
                    TableName: this.tableName,
                    KeySchema: [
                        {
                            AttributeName: 'date',
                            KeyType: 'HASH' // Partition key
                        },
                        {
                            AttributeName: 'hour_subject',
                            KeyType: 'RANGE' // Sort key
                        }
                    ],
                    AttributeDefinitions: [
                        {
                            AttributeName: 'date',
                            AttributeType: 'S'
                        },
                        {
                            AttributeName: 'hour_subject',
                            AttributeType: 'S'
                        }
                    ],
                    BillingMode: 'PAY_PER_REQUEST' // On-demand billing
                };

                await this.dynamodb.createTable(params).promise();

                // Wait for table to be created
                await this.dynamodb.waitFor('tableExists', { TableName: this.tableName }).promise();
                console.log(`Table ${this.tableName} created successfully`);
                return true;
            } else {
                throw error;
            }
        }
    }

    /**
     * Upsert homework items to DynamoDB.
     * Uses conditional updates to only modify items when content has changed.
     * 
     * @param {Array<Object>} items Array of homework item objects
     * @returns {Promise<number>} Number of items actually inserted or updated
     */
    async upsertItems(items) {
        let count = 0;

        for (const item of items) {
            try {
                // Convert to HomeworkItem if it's not already
                const homeworkItem = item instanceof HomeworkItem ? item : new HomeworkItem(item);

                // Generate hour_subject sort key
                const hourSubject = homeworkItem.hourSubjectKey;

                // Prepare item data
                const currentTime = new Date().toISOString();
                const itemData = {
                    date: homeworkItem.date,
                    hour_subject: hourSubject,
                    subject: homeworkItem.subject,
                    description: homeworkItem.description,
                    hour: homeworkItem.hour,
                    due_date: homeworkItem.dueDate,
                    homework_text: homeworkItem.homeworkText,
                    teacher: homeworkItem.teacher,
                    class_description: homeworkItem.classDescription,
                    created_at: homeworkItem.createdAt,
                    updated_at: currentTime
                };

                // Remove null/undefined values
                Object.keys(itemData).forEach(key => {
                    if (itemData[key] === null || itemData[key] === undefined) {
                        delete itemData[key];
                    }
                });

                try {
                    // Try to get existing item
                    const getParams = {
                        TableName: this.tableName,
                        Key: {
                            date: homeworkItem.date,
                            hour_subject: hourSubject
                        }
                    };

                    const response = await this.docClient.get(getParams).promise();
                    const existingItem = response.Item;

                    if (existingItem) {
                        // Check if meaningful content has changed
                        const contentChanged = (
                            (existingItem.homework_text || '') !== (homeworkItem.homeworkText || '') ||
                            (existingItem.description || '') !== homeworkItem.description
                        );

                        if (contentChanged) {
                            // Update existing item
                            const putParams = {
                                TableName: this.tableName,
                                Item: itemData
                            };
                            await this.docClient.put(putParams).promise();
                            count++;
                            console.log(`Updated homework item: ${homeworkItem.date} - ${homeworkItem.subject}`);
                        } else {
                            console.log(`No changes for homework item: ${homeworkItem.date} - ${homeworkItem.subject}`);
                        }
                    } else {
                        // Insert new item
                        const putParams = {
                            TableName: this.tableName,
                            Item: itemData
                        };
                        await this.docClient.put(putParams).promise();
                        count++;
                        console.log(`Inserted new homework item: ${homeworkItem.date} - ${homeworkItem.subject}`);
                    }

                } catch (error) {
                    console.error(`Error upserting item ${homeworkItem.date} - ${homeworkItem.subject}:`, error);
                    continue;
                }

            } catch (error) {
                console.error('Error processing homework item:', error);
                continue;
            }
        }

        console.log(`Upserted ${count} homework items to DynamoDB`);
        return count;
    }

    /**
     * Get all homework items for a specific date.
     * 
     * @param {string} date Date in YYYY-MM-DD format
     * @returns {Promise<Array>} Array of homework items
     */
    async getItemsByDate(date) {
        try {
            const params = {
                TableName: this.tableName,
                KeyConditionExpression: '#date = :date',
                ExpressionAttributeNames: {
                    '#date': 'date'
                },
                ExpressionAttributeValues: {
                    ':date': date
                }
            };

            const response = await this.docClient.query(params).promise();
            const items = response.Items || [];

            // Sort by hour and subject
            items.sort((a, b) => {
                const hourA = a.hour || 'unknown';
                const hourB = b.hour || 'unknown';
                const subjectA = a.subject || '';
                const subjectB = b.subject || '';
                
                if (hourA !== hourB) return hourA.localeCompare(hourB);
                return subjectA.localeCompare(subjectB);
            });

            console.log(`Retrieved ${items.length} items for date ${date}`);
            return items;

        } catch (error) {
            console.error(`Error querying items for date ${date}:`, error);
            return [];
        }
    }

    /**
     * Get all homework items from the table.
     * 
     * @param {number} [limit] Optional limit on number of items to return
     * @returns {Promise<Array>} Array of homework items
     */
    async getAllItems(limit = null) {
        try {
            const params = {
                TableName: this.tableName
            };

            if (limit) {
                params.Limit = limit;
            }

            const response = await this.docClient.scan(params).promise();
            let items = response.Items || [];

            // Handle pagination if needed
            let lastEvaluatedKey = response.LastEvaluatedKey;
            while (lastEvaluatedKey && (!limit || items.length < limit)) {
                const remainingLimit = limit ? limit - items.length : null;
                const scanParams = {
                    TableName: this.tableName,
                    ExclusiveStartKey: lastEvaluatedKey
                };

                if (remainingLimit) {
                    scanParams.Limit = remainingLimit;
                }

                const nextResponse = await this.docClient.scan(scanParams).promise();
                items = items.concat(nextResponse.Items || []);
                lastEvaluatedKey = nextResponse.LastEvaluatedKey;
            }

            // Sort by date, hour, and subject
            items.sort((a, b) => {
                if (a.date !== b.date) return a.date.localeCompare(b.date);
                
                const hourA = a.hour || 'unknown';
                const hourB = b.hour || 'unknown';
                if (hourA !== hourB) return hourA.localeCompare(hourB);
                
                const subjectA = a.subject || '';
                const subjectB = b.subject || '';
                return subjectA.localeCompare(subjectB);
            });

            console.log(`Retrieved ${items.length} total items from DynamoDB`);
            return items;

        } catch (error) {
            console.error('Error scanning all items:', error);
            return [];
        }
    }

    /**
     * Delete a specific homework item.
     * 
     * @param {string} date Date in YYYY-MM-DD format
     * @param {string} hour Hour string
     * @param {string} subject Subject name
     * @returns {Promise<boolean>} True if deleted successfully
     */
    async deleteItem(date, hour, subject) {
        try {
            const hourPart = hour || "unknown";
            const hourSubject = `${hourPart}#${subject}`;

            const params = {
                TableName: this.tableName,
                Key: {
                    date: date,
                    hour_subject: hourSubject
                }
            };

            await this.docClient.delete(params).promise();
            console.log(`Deleted homework item: ${date} - ${subject}`);
            return true;

        } catch (error) {
            console.error(`Error deleting item ${date} - ${subject}:`, error);
            return false;
        }
    }
}

export { HomeworkItem, DynamoDBHandler };