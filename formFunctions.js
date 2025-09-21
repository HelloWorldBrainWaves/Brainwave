/* 
    Function's for BrainWave's User Profile Form
    — localStorage-based. 
*/

// --- static lists
const SUBJECTS = ["CS 180", "CS 240", "CS 251", "MA 165", "MA 166", "PHYS 172", "CHEM 115", "STAT 350"];
const SPACES = ["Library", "Coffee shop", "Online / Zoom", "Classroom", "Dorm Lounges"];
const TRAITS = ["Introvert", "Extrovert", "Planner", "Spontaneous", "Motivated", "Procrastinator"];


// --- helpers to build checkboxes 
function makeCheckbox(id, label) {
    return `<label class="checkBox" style="margin-right:8px;"><input type="checkbox" data-id="${id}" /> ${label}</label>`;
}
document.getElementById('subjectsContainer').innerHTML = SUBJECTS.map((s,i)=>makeCheckbox('sub'+i,s)).join(' ');
document.getElementById('spacesContainer').innerHTML = SPACES.map((s,i)=>makeCheckbox('sp'+i,s)).join(' ');
document.getElementById('traitsContainer').innerHTML = TRAITS.map((s,i)=>makeCheckbox('tr'+i,s)).join(' ');


// --- times list handling ---
const times = [];
document.getElementById('addTime').addEventListener('click', () => {
    const t = document.getElementById('timeInput').value.trim();
    if (!t) return;
    times.push(t);
    document.getElementById('timeInput').value = '';
    renderTimes();
});

function renderTimes() {
        document.getElementById('timesList').textContent = times.join(' · ');
    }


// --- localStorage helpers ---
function loadUsers() {
        return JSON.parse(localStorage.getItem('brainwave_users') || '[]');
    }

function saveUsers(u) { localStorage.setItem('brainwave_users', JSON.stringify(u)); }

function loadRequests() {
        return JSON.parse(localStorage.getItem('brainwave_requests') || '[]');
    }

function saveRequests(r) { localStorage.setItem('brainwave_requests', JSON.stringify(r)); }

    // --- form submit (save profile) ---
    document.getElementById('profileForm').addEventListener('submit', function(e){
        e.preventDefault();
        const user = gatherForm();
        const users = loadUsers();
        // if same email exists, update
        const existingIndex = users.findIndex(x => x.email && x.email.toLowerCase() === user.email.toLowerCase());
        if (existingIndex >= 0) {
        user.id = users[existingIndex].id;
        users[existingIndex] = user;
        } else {
        user.id = Date.now(); // simple id
        users.push(user);
        }
        saveUsers(users);
        localStorage.setItem('brainwave_current_user', String(user.id));
        /* alert('Saved your profile! Your ID: ' + user.id); */
    });

    function testFunction() {
        console.log("TESTs")
    }

    // gather form data into an object
    function gatherForm() {
        function checkedValues(containerId, baseList) {
        const container = document.getElementById(containerId);
        const checks = Array.from(container.querySelectorAll('input[type=checkbox]'));
        const selected = checks.filter(c=>c.checked).map((c,i)=>{
            // match by index in baseList: c.dataset.id contains index suffix, but easiest: use label text
            return c.parentElement.textContent.trim();
        });
        return selected;
        }
        const subjectsOther = document.getElementById('subjectOther').value.trim();
        const subjectsExtra = subjectsOther ? subjectsOther.split(',').map(s=>s.trim()).filter(Boolean) : [];
        return {
        email: document.getElementById('email').value.trim(),
        phone: document.getElementById('phone').value.trim(),
        name: document.getElementById('name').value.trim(),
        year: document.getElementById('year').value,
        major: document.getElementById('major').value.trim(),
        subjects: checkedValues('subjectsContainer').concat(subjectsExtra),
        desired_group_size: document.getElementById('groupSize').value,
        comfort_level: document.getElementById('comfort').value,
        study_space_prefs: checkedValues('spacesContainer'),
        max_distance: Number(document.getElementById('distance').value) || 0,
        available_times: times.slice(),
        personality_traits: checkedValues('traitsContainer'),
        goal: document.getElementById('goal').value.trim(),
        ice_breaker: document.getElementById('ice').value.trim(),
        bio: document.getElementById('bio').value.trim(),
        created_at: Date.now()
        };
    }


// --- view matches ---
document.getElementById('viewMatchesBtn').addEventListener('click', showMatches);
document.getElementById('backToProfile').addEventListener('click', ()=>{ showSection('profileSection'); });
document.getElementById('backToProfile2').addEventListener('click', ()=>{ showSection('profileSection'); });

function showSection(idToShow) {
        ['profileSection','matchesSection','requestsSection'].forEach(id => {
        document.getElementById(id).style.display = (id === idToShow) ? '' : 'none';
        });
    }

function getCurrentUser() {
        const id = localStorage.getItem('brainwave_current_user');
        if (!id) return null;
        const users = loadUsers();
        return users.find(u => String(u.id) === String(id)) || null;
    }

function showMatches() {
        const me = getCurrentUser();
        if (!me) { alert('Please save your profile first.'); return showSection('profileSection'); }
        const users = loadUsers().filter(u => u.id !== me.id);
        const scored = users.map(u => {
        const score = computeScore(me, u);
        return { user: u, score };
        }).sort((a,b)=>b.score.total - a.score.total);
        renderMatches(scored);
        showSection('matchesSection');
    }

function renderMatches(list) {
        const container = document.getElementById('matchesList');
        container.innerHTML = '';
        if (list.length === 0) {
        container.innerHTML = '<div class="muted card">No other profiles found. Try creating multiple sample profiles to test matches.</div>';
        return;
        }
        list.forEach(item => {
        const u = item.user;
        const s = item.score;
        const div = document.createElement('div');
        div.className = 'card matchCard';
        div.innerHTML = `
        <div style="flex:1">
            <div style="display:flex; align-items:center; gap:12px;">
            <strong>${u.name || '(no name)'}</strong>
            <span class="muted">${u.year || ''} • ${u.major || ''}</span>
            </div>
            <div class="muted" style="margin-top:6px;">Subjects: ${ (u.subjects||[]).slice(0,5).join(', ') || '—' }</div>
            <div style="margin-top:6px;">Bio: ${ (u.bio || '').slice(0,160) }</div>
            <div style="margin-top:8px;">
            <span class="chip">Score ${Math.round(s.total)}</span>
            <span class="muted">Subjects match: ${s.subjectsMatched}</span>
            <span class="muted">Times match: ${s.timesMatched}</span>
            </div>
        </div>
        <div class="flex" style="min-width:120px; justify-content:flex-end;">
            <button class="formBtn formBtnDanger" data-action="no" data-id="${u.id}">No</button>
            <button class="formBtn formBtnPimary" data-action="yes" data-id="${u.id}">Yes</button>
        </div>
        `;
        container.appendChild(div);
        });

        container.querySelectorAll('button[data-action]').forEach(b=>{
        b.addEventListener('click', e=>{
            const id = b.dataset.id;
            const action = b.dataset.action;
            if (action === 'yes') {
            sendMatchRequest(id);
            } else {
            // simple "dismiss" UX: remove card from view
            b.closest('.card').remove();
            }
        });
        });
    }


// --- match request handling (stored locally) ---
function sendMatchRequest(toUserId) {
        const me = getCurrentUser();
        if (!me) return alert('Save profile first.');
        const requests = loadRequests();
        // avoid duplicates
        if (requests.some(r => r.from === me.id && String(r.to) === String(toUserId))) {
        alert('You already sent a request to this person.');
        return;
        }
        requests.push({ id: Date.now(), from: me.id, to: String(toUserId), status: 'pending', created_at: Date.now() });
        saveRequests(requests);
        alert('Match request sent!');
    }


// --- incoming requests view ---
document.getElementById('viewRequestsBtn').addEventListener('click', () => {
        const me = getCurrentUser();
        if (!me) { alert('Save profile first.'); return; }
        const requests = loadRequests().filter(r => String(r.to) === String(me.id));
        const users = loadUsers();
        const list = document.getElementById('requestsList');
        list.innerHTML = '';
        if (!requests.length) { list.innerHTML = '<div class="muted card">No requests yet.</div>'; showSection('requestsSection'); return; }
        requests.forEach(req => {
        const fromUser = users.find(u => String(u.id) === String(req.from)) || { name: 'Unknown' };
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
            <strong>${fromUser.name}</strong> <div class="muted">"${fromUser.ice_breaker || ''}"</div>
            <div class="muted">Bio: ${ (fromUser.bio||'') }</div>
            </div>
            <div style="display:flex; gap:8px;">
            <button class="btn btnPrimary" data-accept="${req.id}">Accept</button>
            <button class="btn" data-decline="${req.id}">Decline</button>
            </div>
        </div>
        `;
        list.appendChild(card);
        });
        // attach handlers
        list.querySelectorAll('button[data-accept]').forEach(b=>{
        b.addEventListener('click', () => {
            const id = b.getAttribute('data-accept');
            const requests = loadRequests();
            const idx = requests.findIndex(r => String(r.id) === String(id));
            if (idx >=0) {
            requests[idx].status = 'accepted';
            saveRequests(requests);
            alert('Accepted — you can now message this person (not implemented in demo).');
            showMatches(); // back to matches
            }
        });
        });
        list.querySelectorAll('button[data-decline]').forEach(b=>{
        b.addEventListener('click', () => {
            const id = b.getAttribute('data-decline');
            let requests = loadRequests();
            requests = requests.filter(r => String(r.id) !== String(id));
            saveRequests(requests);
            b.closest('.card').remove();
        });
        });
        showSection('requestsSection');
    });

// matching algorithm
function computeScore(me, other) {
        const score = { total:0, subjectsMatched:0, timesMatched:0 };
        const subjectsA = (me.subjects||[]).map(s => s.toLowerCase());
        const subjectsB = (other.subjects||[]).map(s => s.toLowerCase());
        const subjectsMatched = subjectsA.filter(s => subjectsB.includes(s));
        score.subjectsMatched = subjectsMatched.length;
        score.total += subjectsMatched.length * 5;

        // time overlap (string equality)
        const timesA = (me.available_times||[]).map(t => t.toLowerCase());
        const timesB = (other.available_times||[]).map(t => t.toLowerCase());
        const timesMatched = timesA.filter(t => timesB.includes(t));
        score.timesMatched = timesMatched.length;
        score.total += timesMatched.length * 4;

        // group size similarity
        const ga = Number(me.desired_group_size || 1);
        const gb = Number(other.desired_group_size || 1);
        if (Math.abs(ga - gb) <= 1) score.total += 3;

        // comfort match
        if ((me.comfort_level || '').toLowerCase() && (other.comfort_level || '').toLowerCase()
        && me.comfort_level.toLowerCase() === other.comfort_level.toLowerCase()) score.total += 2;

        // study space prefs
        const prefsA = (me.study_space_prefs||[]).map(s => s.toLowerCase());
        const prefsB = (other.study_space_prefs||[]).map(s => s.toLowerCase());
        const prefsMatched = prefsA.filter(s => prefsB.includes(s));
        score.total += prefsMatched.length * 1.5;

        // personality overlap
        const pA = (me.personality_traits||[]).map(x=>x.toLowerCase());
        const pB = (other.personality_traits||[]).map(x=>x.toLowerCase());
        const pMatched = pA.filter(x => pB.includes(x));
        score.total += pMatched.length * 1;

        // major / year
        if ((me.major||'').toLowerCase() === (other.major||'').toLowerCase()) score.total += 2;
        if ((me.year||'').toLowerCase() === (other.year||'').toLowerCase()) score.total += 2;

        // small boost if user wrote a bio
        if ((other.bio||'').length > 20) score.total += 1;

        return score;
    }


// Fake profiles for local testing
(function seedIfEmpty() {
        const users = loadUsers();
        if (users.length === 0) {
        const demoA = {
            id: 1111, name: 'Alice', email: 'alice@purdue.edu', year:'Junior', major:'CS', subjects:['CS 180','CS 240'],
            desired_group_size:'2', comfort_level:'Quiet', study_space_prefs:['Library'], max_distance:5,
            available_times:['Mon 6-8pm','Wed 6-8pm'], personality_traits:['Planner'], goal:'Understand algorithms', ice_breaker:'Tea or coffee?', bio:'I like quiet study.'
        };
        const demoB = {
            id: 2222, name: 'Bob', email: 'bob@purdue.edu', year:'Junior', major:'CS', subjects:['CS 180','MATH 165'],
            desired_group_size:'3', comfort_level:'Mixed', study_space_prefs:['Coffee shop','Online / Zoom'], max_distance:10,
            available_times:['Mon 6-8pm','Tue 2-4pm'], personality_traits:['Extrovert','Motivated'], goal:'Pass midterms', ice_breaker:'Favorite snack?', bio:'Love group work.'
        };
        users.push(demoA, demoB);
        saveUsers(users);
        // leave current user unset so you can create one
        }
})();
