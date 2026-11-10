/**
 * Hermes Recursive CI Dashboard Frontend
 */

document.addEventListener('DOMContentLoaded', () => {
  fetchResources();
  fetchRepos();
  fetchProposals();

  // Poll for live updates every 5 seconds
  setInterval(() => {
    fetchResources();
    fetchProposals();
  }, 5000);

  // Add Repo Form toggle
  const btnShowAddRepo = document.getElementById('btn-show-add-repo');
  const addRepoForm = document.getElementById('add-repo-form');
  const btnCancelRepo = document.getElementById('btn-cancel-repo');
  const btnSubmitRepo = document.getElementById('btn-submit-repo');

  btnShowAddRepo.addEventListener('click', () => addRepoForm.classList.toggle('hidden'));
  btnCancelRepo.addEventListener('click', () => addRepoForm.classList.add('hidden'));

  btnSubmitRepo.addEventListener('click', async () => {
    const id = document.getElementById('input-repo-id').value.trim();
    const name = document.getElementById('input-repo-name').value.trim();
    const path = document.getElementById('input-repo-path').value.trim();

    if (!id || !path) {
      alert('Please provide Repo ID and Path');
      return;
    }

    try {
      const res = await fetch('/api/v1/repos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, name: name || id, path })
      });
      const data = await res.json();
      if (data.success) {
        addRepoForm.classList.add('hidden');
        fetchRepos();
      } else {
        alert('Error: ' + data.error);
      }
    } catch (e) {
      alert('Network error: ' + e.message);
    }
  });

  // Trigger Sprint Dash
  document.getElementById('btn-trigger-dash').addEventListener('click', async () => {
    const repos = window.activeRepos || [];
    if (repos.length === 0) {
      alert('Please register at least one target repository first.');
      return;
    }
    const repoId = repos[0].id;
    try {
      const res = await fetch('/api/v1/dash', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_id: repoId, batch_size: 3 })
      });
      const data = await res.json();
      if (data.success) {
        fetchProposals();
        fetchResources();
      } else {
        alert('Governance / Preflight note: ' + (data.reason || 'Failed'));
      }
    } catch (e) {
      alert('Network error: ' + e.message);
    }
  });

  // Filter change
  document.getElementById('filter-status').addEventListener('change', () => {
    fetchProposals();
  });
});

async function fetchResources() {
  try {
    const res = await fetch('/api/v1/resources');
    const data = await res.json();
    if (data.success) {
      const r = data.resources;
      document.getElementById('header-tokens').innerText = 
        `${r.tokens_consumed_today.toLocaleString()} / ${r.daily_token_quota.toLocaleString()} (${r.quota_utilization_pct}%)`;
    }
  } catch (e) {}
}

async function fetchRepos() {
  try {
    const res = await fetch('/api/v1/repos');
    const data = await res.json();
    if (data.success) {
      window.activeRepos = data.repos;
      document.getElementById('stat-repo-count').innerText = data.repos.length;
      renderRepos(data.repos);
    }
  } catch (e) {}
}

function renderRepos(repos) {
  const container = document.getElementById('repo-list');
  container.innerHTML = '';

  if (repos.length === 0) {
    container.innerHTML = `<div class="text-xs text-zinc-500 font-mono col-span-2">No target repositories registered yet. Add one above!</div>`;
    return;
  }

  repos.forEach(repo => {
    const card = document.createElement('div');
    card.className = 'p-4 bg-zinc-900 border border-zinc-800 rounded-xl space-y-3';
    card.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="font-bold text-sm text-white font-mono">${repo.name}</span>
        <span class="px-2 py-0.5 rounded text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          Health: ${repo.health_score || 80}%
        </span>
      </div>
      <div class="text-xs text-zinc-400 font-mono truncate">Path: ${repo.path}</div>
      <div class="flex items-center justify-between text-xs text-zinc-500 pt-2 border-t border-zinc-800/60">
        <span>Branch: <b class="text-zinc-300 font-mono">${repo.default_branch}</b></span>
        <button onclick="triggerRepoDash('${repo.id}')" class="text-xs text-emerald-400 hover:underline font-mono">Run Dash</button>
      </div>
    `;
    container.appendChild(card);
  });
}

async function triggerRepoDash(repoId) {
  const res = await fetch('/api/v1/dash', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_id: repoId, batch_size: 2 })
  });
  const data = await res.json();
  if (data.success) {
    fetchProposals();
  } else {
    alert('Notice: ' + (data.reason || 'Could not trigger dash'));
  }
}

async function fetchProposals() {
  const status = document.getElementById('filter-status').value;
  let url = '/api/v1/proposals';
  if (status) url += `?status=${status}`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.success) {
      updateProposalStats(data.proposals);
      renderProposals(data.proposals);
    }
  } catch (e) {}
}

function updateProposalStats(proposals) {
  let pending = 0, verified = 0, snoozed = 0;
  proposals.forEach(p => {
    if (p.status === 'PROPOSED' || p.status === 'AWAITING_ANSWERS') pending++;
    else if (p.status === 'TESTS_PASSED' || p.status === 'MERGED') verified++;
    else if (p.status === 'SNOOZED') snoozed++;
  });
  document.getElementById('stat-pending-count').innerText = pending;
  document.getElementById('stat-verified-count').innerText = verified;
  document.getElementById('stat-snoozed-count').innerText = snoozed;
}

function renderProposals(proposals) {
  const container = document.getElementById('proposals-list');
  container.innerHTML = '';

  if (proposals.length === 0) {
    container.innerHTML = `<div class="p-6 bg-zinc-900/30 border border-zinc-800 rounded-xl text-center text-xs text-zinc-500 font-mono">No proposals found for current filter.</div>`;
    return;
  }

  proposals.forEach(prop => {
    let badgeClass = 'badge-proposed';
    if (prop.status === 'TESTS_PASSED') badgeClass = 'badge-passed';
    else if (prop.status === 'SNOOZED') badgeClass = 'badge-snoozed';
    else if (prop.status === 'REJECTED') badgeClass = 'badge-rejected';

    const card = document.createElement('div');
    card.className = 'p-5 bg-zinc-900 border border-zinc-800 rounded-xl space-y-3';
    card.innerHTML = `
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="text-xs px-2 py-0.5 rounded font-mono ${badgeClass}">${prop.status}</span>
          <span class="text-xs px-2 py-0.5 rounded font-mono bg-zinc-800 text-zinc-400">${prop.type.toUpperCase()}</span>
          <h3 class="font-bold text-sm text-white">${prop.title}</h3>
        </div>
        <div class="flex items-center gap-3 text-xs font-mono text-zinc-400">
          <span>Safety: <b class="text-emerald-400">${(prop.safety_score * 100).toFixed(0)}%</b></span>
          <span>Delta Score: <b class="text-indigo-400">${prop.semantic_delta_score}</b></span>
        </div>
      </div>

      <p class="text-xs text-zinc-300">${prop.rationale || 'No rationale provided.'}</p>
      
      <div class="p-2 bg-zinc-950 border border-zinc-800 rounded text-xs font-mono text-zinc-400">
        <span class="text-zinc-500">Proposed Diff:</span> ${prop.proposed_diff_summary || 'N/A'}
      </div>

      <div class="flex items-center justify-between pt-2 border-t border-zinc-800/80">
        <div class="text-xs text-zinc-500 font-mono">ID: ${prop.id} | Repo: ${prop.repo_id}</div>
        <div class="flex items-center gap-2">
          ${prop.status === 'PROPOSED' ? `
            <button onclick="approveProposal('${prop.id}')" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs rounded transition">
              ✅ Approve (Run CI)
            </button>
            <button onclick="snoozeProposal('${prop.id}')" class="px-3 py-1 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/40 font-mono text-xs rounded transition">
              ⏳ Snooze +24h
            </button>
            <button onclick="rejectProposal('${prop.id}')" class="px-3 py-1 bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 border border-rose-500/40 font-mono text-xs rounded transition">
              ❌ Reject
            </button>
          ` : ''}
          ${prop.status === 'AWAITING_ANSWERS' ? `
            <button onclick="answerProposal('${prop.id}')" class="px-3 py-1 bg-amber-600 hover:bg-amber-500 text-white font-mono text-xs rounded transition">
              💬 Answer Clarifications
            </button>
          ` : ''}
          ${prop.status === 'TESTS_PASSED' ? `
            <button onclick="mergeProposal('${prop.id}')" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs rounded transition">
              🚀 Create Branch / Merge
            </button>
          ` : ''}
          ${prop.status === 'MERGED' ? `
            <span class="text-xs font-mono text-emerald-400">✔ Branch ${prop.branch_name || 'rec-ci'} (${prop.commit_sha || 'merged'})</span>
          ` : ''}
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

async function approveProposal(id) {
  const notes = prompt('Add optional implementation guidance or maintainer notes:');
  const res = await fetch(`/api/v1/proposals/${id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes: notes || '' })
  });
  const data = await res.json();
  if (data.status === 'AWAITING_ANSWERS' && Array.isArray(data.clarifying_questions)) {
    alert('Clarification required:\n- ' + data.clarifying_questions.join('\n- '));
  } else {
    alert(data.message || 'Execution finished');
  }
  fetchProposals();
  fetchResources();
}

async function answerProposal(id) {
  const answers = prompt('Enter your answers to the clarifying questions (one per line):');
  if (!answers) return;
  const res = await fetch(`/api/v1/proposals/${id}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers })
  });
  const data = await res.json();
  alert(data.message || 'Answers submitted');
  fetchProposals();
  fetchResources();
}

async function mergeProposal(id) {
  const res = await fetch(`/api/v1/proposals/${id}/merge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ merge_to_base: false })
  });
  const data = await res.json();
  alert(data.message || 'Branch created');
  fetchProposals();
}

async function rejectProposal(id) {
  const rationale = prompt('Why is this feature or mutation not useful? (This will train the agent to avoid future duplicates):');
  if (!rationale) return;
  const res = await fetch(`/api/v1/proposals/${id}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rationale })
  });
  const data = await res.json();
  if (data.success) {
    fetchProposals();
  }
}

async function snoozeProposal(id) {
  const res = await fetch(`/api/v1/proposals/${id}/snooze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ duration_hours: 24 })
  });
  const data = await res.json();
  if (data.success) {
    fetchProposals();
  }
}
