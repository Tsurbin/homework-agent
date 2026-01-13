import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

let cachedSecrets: Record<string, string> | null = null;

export async function getSecrets(): Promise<Record<string, string>> {
  // Return cached secrets if available
  if (cachedSecrets) {
    return cachedSecrets;
  }

  const secretName = process.env.AWS_SECRET_NAME || 'homework-agent/secrets';
  const region = process.env.AWS_REGION || 'us-east-1';

  const client = new SecretsManagerClient({ 
    region,
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!
    }
  });

  try {
    const response = await client.send(
      new GetSecretValueCommand({
        SecretId: secretName,
      })
    );

    if (response.SecretString) {
      cachedSecrets = JSON.parse(response.SecretString);
      return cachedSecrets!;
    }

    throw new Error('Secret value is empty');
  } catch (error) {
    console.error('Error fetching secrets from AWS Secrets Manager:', error);
    // Fallback to environment variables for local development
    return {
      ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY || ''
    };
  }
}

export async function getSecret(key: string): Promise<string | undefined> {
  const secrets = await getSecrets();
  return secrets[key];
}
