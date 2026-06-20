// Layer 3 Tool — picks Jira vs Azure DevOps as the ticket source. Atomic.
import { fetchIssue } from './jiraClient.js';
import { fetchWorkItem } from './azureDevOpsClient.js';

export async function fetchTicket(config, id) {
  if (config.dataSource === 'azure') return fetchWorkItem(config, id);
  return fetchIssue(config, id);
}
