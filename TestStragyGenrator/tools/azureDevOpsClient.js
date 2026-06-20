// Layer 3 Tool — Azure DevOps work item fetch + normalize. Atomic, deterministic.
// Normalizes to the same shape jiraClient.normalizeIssue produces so downstream
// generation code (test plan / cases / scripts) is data-source-agnostic.

export function normalizeWorkItem(raw) {
  const f = raw.fields || {};
  const description = (f['System.Description'] || '').replace(/<[^>]+>/g, ' ').replace(/\s{2,}/g, ' ').trim();

  return {
    key: `${f['System.TeamProject'] || ''}#${raw.id}`,
    summary: f['System.Title'] || '',
    description: description || '',
    issueType: f['System.WorkItemType'] || 'Unknown',
    status: f['System.State'] || 'Unknown',
    priority: f['Microsoft.VSTS.Common.Priority'] != null ? String(f['Microsoft.VSTS.Common.Priority']) : 'Unspecified',
    components: (f['System.AreaPath'] ? [f['System.AreaPath']] : []),
    labels: f['System.Tags'] ? f['System.Tags'].split(';').map((t) => t.trim()).filter(Boolean) : [],
    fixVersions: f['System.IterationPath'] ? [f['System.IterationPath']] : [],
    reporter: f['System.CreatedBy']?.displayName || 'Unknown',
    assignee: f['System.AssignedTo']?.displayName || null,
  };
}

export async function fetchWorkItem(config, workItemId) {
  const azure = config.azure || {};
  const base = (azure.orgUrl || '').trim().replace(/\/+$/, '');
  if (!base) throw new Error('Missing Azure DevOps organization URL');
  if (!azure.project) throw new Error('Missing Azure DevOps project');
  if (!azure.pat) throw new Error('Missing Azure DevOps personal access token');
  if (!workItemId) throw new Error('Missing work item ID');

  const url = `${base}/${encodeURIComponent(azure.project)}/_apis/wit/workitems/${encodeURIComponent(workItemId)}?api-version=7.1`;
  const auth = Buffer.from(`:${azure.pat}`).toString('base64');

  const res = await fetch(url, {
    headers: { Authorization: `Basic ${auth}`, Accept: 'application/json' },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Azure DevOps ${res.status} fetching ${workItemId}: ${body.slice(0, 300)}`);
  }

  return normalizeWorkItem(await res.json());
}
