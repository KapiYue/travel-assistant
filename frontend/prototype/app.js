const SAMPLE_REQUEST = '明天准备去三亚玩三天，我们跟我对象，想要玩海上项目，帮我规划下行程和酒店';

const ROUTES = [
  { title: '1日佛光普照的海岸线之旅', path: '南山寺 → 三亚南山别院 → 南山海上观音 → 大小洞天', place: '大东海旅游区' },
  { title: '1日佛光普照的海岸线之旅', path: '南山寺 → 南山文化旅游区 → 南山海上观音 → 三亚湾', place: '南山文化旅游区' },
  { title: '1日三亚湾城市漫步', path: '椰梦长廊 → 三亚湾海滩 → 凤凰岛', place: '三亚湾海滩' },
  { title: '1日西岛日落·三亚湾椰影', path: '西岛 → 海岸步道 → 三亚湾日落', place: '西岛海滨' },
];

const AGENTS = [
  { name: '路线定制师', icon: '👁️', copy: '正在查询相关的旅行路线' },
  { name: '攻略达人', icon: '🥥', copy: '整理景点、美食与海上项目的候选安排' },
  { name: '智慧交通顾问', icon: '🌐', copy: '梳理往返交通与行程间的接驳方式' },
];

const $ = (selector, root = document) => root.querySelector(selector);
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[char]));

function sampleDays(destination = '三亚', source = '长沙', count = 3) {
  const sanya = destination === '三亚';
  const days = [
    {
      title: '海滨初体验',
      events: [
        { id: 'flight-out', kind: '交通', type: 'flight', title: `乘坐飞机 11月13日 ${source} - ${destination}`, place: `${source} → ${destination}`, time: '10:00 - 12:30', reason: '飞行时间短，上午出发到达后有充足的时间游玩', flight: { from: '10:00', to: '12:30', fromPort: '黄花T2', toPort: '凤凰T1', code: '华夏 G55068', price: '¥1190' } },
        { id: 'lunch-1', kind: '午餐', title: sanya ? '椰梦·海鲜糟粕醋·椰子鸡' : `${destination}当地特色午餐`, place: sanya ? '椰梦·海鲜糟粕醋·椰子鸡(大东海店)' : `${destination}餐厅待选`, time: '13:30 - 14:30', reason: sanya ? '品尝海南特色糟粕醋火锅，搭配新鲜海鲜和文昌鸡，酸辣开胃，体验当地风味' : '在当地选择方便抵达的餐厅，具体营业信息待确认。' },
        { id: 'sea-1', kind: '下午', title: sanya ? '大东海海滨体验' : `${destination}下午自由探索`, place: sanya ? '大东海旅游区' : `${destination}活动地点待选`, time: '15:00 - 18:00', badge: sanya ? '三亚沙滩海岛景点榜·第3名　3096人感兴趣' : '', reason: sanya ? '三亚著名海湾，水清沙白，适宜游泳、潜水等水上活动，享受热带海滨风光' : '按旅行偏好安排下午活动，地点和开放情况待核实。' },
        { id: 'hotel-1', kind: '住宿', title: sanya ? '海滨酒店候选' : `${destination}住宿候选`, place: sanya ? '大东海 / 三亚湾' : `${destination}住宿区域待选`, time: '晚上', reason: '优先选择交通便利的区域；房价和房态均需另行确认。' },
      ],
    },
    {
      title: '海岛探索',
      events: [
        { id: 'breakfast-2', kind: '早餐', title: '酒店早餐与活动准备', place: '入住酒店', time: '08:00 - 09:00', reason: '准备防晒用品，并确认当天海况与活动安全要求。' },
        { id: 'island-2', kind: '上午', title: sanya ? '海岛与海上项目候选' : `${destination}特色活动`, place: sanya ? '蜈支洲岛方向' : `${destination}待选景点`, time: '09:30 - 12:00', reason: '优先考虑符合偏好的活动；开放、票价和海况需出行前确认。' },
        { id: 'lunch-2', kind: '午餐', title: '轻松午餐与休息', place: sanya ? '海棠湾周边' : `${destination}餐厅待选`, time: '12:30 - 13:30', reason: '预留午间休息时间，避免连续高强度活动。' },
        { id: 'coast-2', kind: '下午', title: '海岸漫步与自由活动', place: sanya ? '海棠湾' : `${destination}活动地点待选`, time: '14:30 - 17:30', reason: '保留弹性时间，方便按天气和体力调整。' },
      ],
    },
    {
      title: '悠闲返程',
      events: [
        { id: 'morning-3', kind: '上午', title: '海景早餐与轻松散步', place: '酒店周边', time: '09:00 - 11:00', reason: '返程当天放慢节奏，避免因活动过满错过交通。' },
        { id: 'lunch-3', kind: '午餐', title: '当地风味午餐', place: sanya ? '三亚市区' : `${destination}餐厅待选`, time: '11:30 - 12:30', reason: '根据返程时间选择方便的用餐地点。' },
        { id: 'return-3', kind: '交通', title: `返回${source}`, place: `${destination} → ${source}`, time: '返程时段待确认', reason: '具体班次、票价与库存均未实时查询。' },
      ],
    },
  ];
  while (days.length < count) {
    const number = days.length + 1;
    days.splice(days.length - 1, 0, {
      title: '自在探索',
      events: [
        { id: `morning-${number}`, kind: '上午', title: `${destination}当地探索`, place: `${destination}地点待选`, time: '09:00 - 12:00', reason: '按兴趣选择活动，具体地点与开放时间待确认。' },
        { id: `afternoon-${number}`, kind: '下午', title: '自由活动', place: `${destination}地点待选`, time: '14:00 - 17:00', reason: '给行程留出调整空间。' },
      ],
    });
  }
  return count === 2 ? [days[0], days[2]] : days.slice(0, count);
}

const state = {
  request: SAMPLE_REQUEST,
  destination: '三亚',
  source: '长沙',
  budget: '待补充',
  people: '2人 · 情侣',
  preference: '海上项目',
  dayCount: 3,
  days: sampleDays(),
  selectedRoute: 0,
  activeAgent: 0,
  focus: 'brief',
  collapsed: { thinking: false, requirements: false, destination: false, membership: false },
  saved: new Set(),
  modal: null,
  editId: null,
  editDay: null,
  toastTimer: null,
  customId: 0,
};

function parseRequest(value) {
  const known = value.match(/(?:去|到|玩|游)(北京|上海|三亚|成都|杭州|厦门|青岛|长沙|广州|深圳|西安|南京|重庆|昆明|大理|丽江|苏州)/);
  const other = value.match(/(?:去|到)([\u4e00-\u9fa5]{2,8}?)(?=玩|旅游|旅行|度假|待|[两二三四五六七2-7]天|，|,|。|$)/);
  state.destination = known?.[1] || other?.[1] || '目的地待补充';
  const count = value.match(/([2-7两二三四五六七])\s*(?:天|日)/);
  const chinese = { 两: 2, 二: 2, 三: 3, 四: 4, 五: 5, 六: 6, 七: 7 };
  state.dayCount = count ? Number(chinese[count[1]] || count[1]) : 3;
  const origin = value.match(/从(北京|上海|长沙|广州|深圳|成都|杭州|重庆|武汉|南京)出发/);
  state.source = origin?.[1] || state.source;
  const budget = value.match(/(?:预算|人均)[约大概\s]*(\d{3,6})/);
  state.budget = budget ? `约 ¥${budget[1]}` : '待补充';
  state.people = /对象|情侣|伴侣|男友|女友/.test(value) ? '2人 · 情侣' : /亲子|孩子|小孩/.test(value) ? '家庭出行' : '人数待补充';
  state.preference = /海|潜水|冲浪|帆船/.test(value) ? '海上项目' : /美食|吃/.test(value) ? '当地美食' : '自由探索';
  state.days = sampleDays(state.destination, state.source, state.dayCount);
  state.saved.clear();
  state.selectedRoute = 0;
}

function header(stage) {
  const time = stage === 'brief' ? '16:17' : stage === 'research' ? '16:24' : '16:25';
  return `<div class="status-bar"><span>${time} ☾</span><span class="island" aria-hidden="true"></span><span class="status-icons"><span>▂▄▆</span><span>◉</span><span class="battery">79</span></span></div>
    <header class="topbar">
      <button class="top-icon" data-action="menu" aria-label="打开菜单"><svg viewBox="0 0 28 28" width="26" height="26" aria-hidden="true"><g fill="currentColor"><circle cx="4" cy="7" r="1.5"/><circle cx="4" cy="14" r="1.5"/><circle cx="4" cy="21" r="1.5"/></g><g stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M9 7h15M9 14h15M9 21h15"/></g></svg></button>
      <div class="top-tabs">
        <button class="top-tab active" data-goto="brief"><span class="ai-mark">AI!</span>问一问</button>
        <button class="top-tab" data-goto="research">推荐</button>
        <button class="top-tab sale" data-action="promotion">双11</button>
      </div>
      <button class="location" data-action="conditions"><span class="pin" aria-hidden="true"></span>${escapeHtml(state.source)}⌄</button>
      <button class="collection" data-action="favorites" aria-label="查看我的收藏"><svg class="collection-icon" viewBox="0 0 32 32" width="25" height="25" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M6 10h21l-2 17H8L6 10ZM11 10V7a5 5 0 0 1 10 0v3"/><path d="m16.5 14 1.2 2.6 2.9.3-2.2 1.9.7 2.9-2.6-1.5-2.6 1.5.7-2.9-2.2-1.9 2.9-.3z"/></svg>我的收藏</button>
    </header>`;
}

function composer(stage) {
  return `<form class="composer" data-composer="${stage}">
    <button class="camera" type="button" data-action="camera" aria-label="相机输入"><svg viewBox="0 0 28 28" width="23" height="23" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true"><path d="M4 8h5l2-2h6l2 2h5v15H4z" stroke-linejoin="round"/><circle cx="14" cy="15" r="5"/></svg></button>
    <div class="input-shell"><input name="request" aria-label="旅行问题" placeholder="有什么旅行问题问问我吧" autocomplete="off" />
      <button class="send" type="button" data-action="voice" aria-label="语音输入"><svg viewBox="0 0 28 28" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" aria-hidden="true"><path d="M7 11v6M11 8v12M15 5v18M19 8v12M23 11v6"/></svg></button></div>
  </form>`;
}

function floatingActions(stage) {
  return `<div class="floating-actions"><button class="new-chat" data-action="new-chat" aria-label="新建对话"><span>⊕</span>新建<br>对话</button><button class="scroll-bottom" data-action="scroll-bottom" data-stage="${stage}" aria-label="滚动到底部">↓</button></div>`;
}

function sectionHeading(label, section) {
  const folded = state.collapsed[section];
  return `<div class="section-head"><span class="left"><span class="tick">✓</span>${label}</span>
    <button class="chevron" data-toggle="${section}" aria-label="${folded ? '展开' : '收起'}${label}">${folded ? '⌄' : '⌃'}</button></div>`;
}

function agentPills() {
  return `<div class="agent-pills">${AGENTS.map((agent, index) => `<button class="agent-pill ${state.activeAgent === index ? 'active' : ''}" data-agent="${index}"><span>${agent.icon}</span>${agent.name}</button>`).join('')}</div>`;
}

function briefContent() {
  if (!state.request) return `<div class="empty-request">新的对话已开始。<br>在底部输入旅行想法，或点击推荐填入示例。</div>
    <button class="thinking" data-action="sample">填入三亚三日行程示例 <span>›</span></button>`;
  return `<div class="message-time">16:15</div>
    <div class="user-bubble">${escapeHtml(state.request)}</div>
    <button class="thinking" data-toggle="thinking"><span>思考已完成</span><span class="muted-action">${state.collapsed.thinking ? '展开 ⌄' : '收起 ⌃'}</span></button>
    ${!state.collapsed.thinking ? `${sectionHeading('已完成用户需求理解和任务拆分', 'requirements')}
      ${!state.collapsed.requirements ? `<div class="assistant-card"><div class="assistant-title"><span class="assistant-avatar">👁️</span>行程助手</div>
      <p>用户想了解明天出发去${escapeHtml(state.destination)}玩${state.dayCount}天的行程，对象同行，想要体验${escapeHtml(state.preference)}。接下来会由多个旅行助手，从交通、景点、线路、酒店等多个方面去进行信息收集。</p>
      <ul><li>确认出发时间（明天）及目的地为${escapeHtml(state.destination)}</li><li>查询适合情侣游玩的海上项目（如潜水、摩托艇、帆船等）</li><li>根据${state.dayCount}天时间安排合理的行程路线，确保有足够时间体验海上活动</li><li>查询到达${escapeHtml(state.destination)}的合适交通方式</li><li>根据行程推荐适合情侣入住的海滨酒店或度假村</li><li>汇总旅行注意事项，生成完整的${state.dayCount}日行程计划</li></ul>
      <div class="continue-row"><button class="text-link" data-action="conditions">补充旅行条件 ›</button></div></div>` : ''}` : ''}
    ${sectionHeading('已完成目的地旅行信息查询', 'destination')}
    ${!state.collapsed.destination ? `${agentPills()}<div class="assistant-card compact"><div class="assistant-title"><span class="assistant-avatar">🌐</span>目的地助手</div><p>目的地信息已经整理成路线和活动候选，可继续查看各助手的建议。</p><button class="text-link" data-goto="research">查看路线与助手建议 →</button></div>` : ''}
    <p class="inline-note">示例草案 · 交通、价格及开放信息未实时核实</p>`;
}

function routeCards() {
  return `<div class="route-panel"><div class="route-title">行程路线</div><div class="routes">
    ${ROUTES.map((route, index) => `<button class="route-card ${state.selectedRoute === index ? 'selected' : ''}" data-route="${index}" aria-label="选择${escapeHtml(route.title)}"><span class="route-card-title">${escapeHtml(route.title)}</span><span class="route-card-path">${escapeHtml(route.path)}</span></button>`).join('')}
    </div></div>`;
}

function researchContent() {
  if (!state.request) return `<div class="empty-request">先在“问一问”里输入旅行需求，再查看路线建议。</div>`;
  const agent = AGENTS[state.activeAgent];
  return `<div class="research-lead">需求已拆分，正在汇总各助手的建议…</div>
    ${sectionHeading('已完成目的地旅行信息查询', 'destination')}
    ${!state.collapsed.destination ? `${agentPills()}<div class="assistant-card research-card"><div class="assistant-title"><span class="assistant-avatar">${agent.icon}</span>${agent.name}</div>
    <p class="query">•　${agent.copy}</p>
    ${state.activeAgent === 0 ? routeCards() : state.activeAgent === 1 ? `<div class="route-panel"><div class="route-title">游玩建议</div><ul><li>海上活动按天气和海况决定，出行前确认安全要求</li><li>午餐优先选择与下午景点顺路的区域</li><li>首日预留交通、入住和休息时间</li></ul></div>` : `<div class="route-panel"><div class="route-title">交通建议</div><ul><li>演示航班：${escapeHtml(state.source)} → ${escapeHtml(state.destination)}</li><li>航班时刻、价格、库存均需实时核实</li><li>预留机场接驳时间，返程班次待确认</li></ul></div>`}
    <div class="continue-row"><button class="text-link" data-goto="itinerary">查看完整行程 →</button></div></div>` : ''}
    <div class="member-section">${sectionHeading('已完成会员权益和优惠信息查询', 'membership')}
    ${!state.collapsed.membership ? `<div class="assistant-card member-card"><div class="assistant-title"><span class="assistant-avatar">👁️</span>会员助手</div><p>•　根据会员身份，查看交通和酒店可用的会员权益与优惠信息。</p><p class="subtle">原型未连接会员账户，以下不展示实际优惠或折扣。</p></div>` : ''}</div>
    <p class="inline-note">路线与权益均为演示内容，请以官方实时信息为准。</p>`;
}

function eventCard(event, dayIndex) {
  const saved = state.saved.has(event.id);
  const heading = `<div class="timeline-heading"><strong>${escapeHtml(event.kind)}</strong><button class="star ${saved ? 'saved' : ''}" data-favorite="${escapeHtml(event.id)}" aria-label="${saved ? '取消收藏' : '收藏'}${escapeHtml(event.title)}">${saved ? '★' : '☆'}</button></div>`;
  if (event.type === 'flight') return `<div class="timeline-item">${heading}<div class="description">${escapeHtml(event.title)} <span class="inline-note">示例</span></div>
    <div class="ticket"><div class="ticket-line"><div class="ticket-time">${escapeHtml(event.flight.from)}<small>${escapeHtml(event.flight.fromPort)}</small></div><div class="ticket-duration">总2h30m</div><div class="ticket-time">${escapeHtml(event.flight.to)}<small>${escapeHtml(event.flight.toPort)}</small></div><div class="ticket-price">${escapeHtml(event.flight.price)}<small>示例价格</small></div></div>
    <div class="ticket-bottom"><span>✈ ${escapeHtml(event.flight.code)}</span><button class="reserve" data-action="reserve">预订</button></div></div>
    <p class="reason"><strong>推荐理由：</strong>${escapeHtml(event.reason)}</p></div>`;
  return `<div class="timeline-item">${heading}<div class="place-line"><span class="place-pill"><span>📍</span><span class="truncate">${escapeHtml(event.place)}</span><button class="edit-place" data-edit-event="${escapeHtml(event.id)}" aria-label="编辑${escapeHtml(event.title)}">✎</button></span></div>
    ${event.badge ? `<div class="local-badge">♙ ${escapeHtml(event.badge)}</div>` : ''}
    <div class="event-time">${escapeHtml(event.time)}</div>
    <p class="reason"><strong>推荐理由：</strong>${escapeHtml(event.reason)}</p></div>`;
}

function itineraryContent() {
  if (!state.request) return `<div class="empty-request">发送旅行需求后，这里会展示逐日行程。</div>`;
  return `${state.days.map((day, index) => `<section class="day-block" id="day-${index}"><div class="day-head"><h2>Day ${index + 1} ${escapeHtml(day.title)}</h2><button class="day-edit" data-edit-day="${index}" aria-label="编辑第${index + 1}天主题">✎</button></div>
    <div class="itinerary-card">${day.events.map(event => eventCard(event, index)).join('')}
    <button class="add-item" data-add-event="${index}">＋ 添加行程安排</button></div></section>`).join('')}
    <p class="inline-note">以上是可编辑的演示草案。航班、餐厅、景区、酒店及价格均未实时核实。</p>`;
}

function phone(stage) {
  const content = stage === 'brief' ? briefContent() : stage === 'research' ? researchContent() : itineraryContent();
  return `<section class="phone ${state.focus === stage ? 'active' : ''}" data-phone="${stage}" aria-label="${stage === 'brief' ? '需求拆分' : stage === 'research' ? '助手查询' : '逐日行程'}">
    ${header(stage)}<div class="feed" data-feed="${stage}">${content}</div>${floatingActions(stage)}${composer(stage)}</section>`;
}

function render(options = {}) {
  const positions = Object.fromEntries([...document.querySelectorAll('[data-feed]')].map(feed => [feed.dataset.feed, feed.scrollTop]));
  $('#app').innerHTML = `<div class="stage"><div class="phones">${['brief', 'research', 'itinerary'].map(phone).join('')}</div>
    <nav class="mobile-switch" aria-label="切换原型画面">${['brief', 'research', 'itinerary'].map((stage, index) => `<button data-goto="${stage}" class="${state.focus === stage ? 'active' : ''}" aria-label="${['需求拆分', '助手查询', '逐日行程'][index]}">${index + 1}</button>`).join('')}</nav></div>
    <div id="modal-host"></div><div id="toast-host"></div>`;
  document.querySelectorAll('[data-feed]').forEach(feed => { feed.scrollTop = options.top === feed.dataset.feed ? 0 : positions[feed.dataset.feed] || 0; });
  renderModal();
}

function showToast(message) {
  $('#toast-host').innerHTML = `<div class="toast" role="status">${escapeHtml(message)}</div>`;
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => { const host = $('#toast-host'); if (host) host.innerHTML = ''; }, 2600);
}

function openModal(type, payload = {}) { state.modal = { type, ...payload }; renderModal(); }
function closeModal() { state.modal = null; renderModal(); }

function renderModal() {
  const host = $('#modal-host');
  if (!host || !state.modal) { if (host) host.innerHTML = ''; return; }
  const { type } = state.modal;
  let title = '', content = '';
  if (type === 'conditions') {
    title = '补充旅行条件';
    content = `<form id="conditions-form"><div class="field-grid"><label class="field">出发城市<input name="source" maxlength="20" value="${escapeHtml(state.source)}" required /></label><label class="field">目的地<input name="destination" maxlength="20" value="${escapeHtml(state.destination)}" required /></label></div>
      <div class="field-grid"><label class="field">行程天数<select name="dayCount">${[2,3,4,5,6,7].map(n => `<option value="${n}" ${state.dayCount === n ? 'selected' : ''}>${n}天</option>`).join('')}</select></label><label class="field">预算<input name="budget" maxlength="30" value="${state.budget === '待补充' ? '' : escapeHtml(state.budget)}" placeholder="待补充" /></label></div>
      <label class="field">同行人<input name="people" maxlength="30" value="${escapeHtml(state.people)}" /></label><label class="field">旅行偏好<input name="preference" maxlength="40" value="${escapeHtml(state.preference)}" /></label>
      <div class="dialog-actions"><button type="button" class="secondary" data-action="close-modal">取消</button><button type="submit" class="primary">保存条件</button></div></form>`;
  } else if (type === 'edit-day') {
    title = `编辑 Day ${state.modal.day + 1} 主题`;
    content = `<form id="day-form"><label class="field">主题名称<input name="title" maxlength="25" value="${escapeHtml(state.days[state.modal.day].title)}" required /></label><div class="dialog-actions"><button type="button" class="secondary" data-action="close-modal">取消</button><button type="submit" class="primary">保存</button></div></form>`;
  } else if (type === 'edit-event') {
    const { day, event } = findEvent(state.modal.id);
    title = '编辑行程安排';
    content = `<form id="event-form"><label class="field">分类<input name="kind" maxlength="20" value="${escapeHtml(event.kind)}" required /></label><label class="field">名称<input name="title" maxlength="50" value="${escapeHtml(event.title)}" required /></label>
      <div class="field-grid"><label class="field">时间<input name="time" maxlength="35" value="${escapeHtml(event.time)}" required /></label><label class="field">地点<input name="place" maxlength="55" value="${escapeHtml(event.place)}" required /></label></div>
      <label class="field">推荐理由<textarea name="reason" maxlength="220">${escapeHtml(event.reason)}</textarea></label><div class="dialog-actions"><button type="button" class="danger" data-action="delete-event">删除</button><button type="button" class="secondary" data-action="close-modal">取消</button><button type="submit" class="primary">保存</button></div></form>`;
  } else if (type === 'add-event') {
    title = `添加 Day ${state.modal.day + 1} 安排`;
    content = `<form id="event-form"><label class="field">分类<input name="kind" maxlength="20" value="活动" required /></label><label class="field">名称<input name="title" maxlength="50" placeholder="例如：海边散步" required /></label><div class="field-grid"><label class="field">时间<input name="time" maxlength="35" placeholder="15:00 - 17:00" required /></label><label class="field">地点<input name="place" maxlength="55" value="${escapeHtml(state.destination)}" required /></label></div><label class="field">推荐理由<textarea name="reason" maxlength="220" placeholder="说明推荐原因"></textarea></label><div class="dialog-actions"><button type="button" class="secondary" data-action="close-modal">取消</button><button type="submit" class="primary">添加</button></div></form>`;
  } else if (type === 'favorites') {
    title = '我的收藏';
    const saved = [...state.saved].map(findEvent).filter(Boolean);
    content = saved.length ? `<ul class="dialog-list">${saved.map(({ day, event }) => `<li><button data-jump-day="${day}" data-action="jump-day">查看</button><strong>${escapeHtml(event.title)}</strong><div class="inline-note">Day ${day + 1} · ${escapeHtml(event.place)}</div></li>`).join('')}</ul>` : `<div class="dialog-copy">还没有收藏。点击行程旁的 ☆，即可加入收藏。</div>`;
  } else if (type === 'reserve') {
    title = '航班预订演示';
    content = `<div class="dialog-copy"><p>图中的班次、时间和 ¥1190 为界面示例，未查询实时票价、库存，也无法在此完成预订。</p><p>正式产品接入可信航班服务后，才能提供可预订的选项。</p></div><div class="dialog-actions"><button class="primary" data-action="close-modal">知道了</button></div>`;
  } else if (type === 'menu') {
    title = '旅行助手';
    content = `<div class="dialog-copy"><p>点击下面的步骤可查看这段对话的不同画面：</p></div><ul class="dialog-list"><li><button data-goto="brief">查看</button>需求理解与任务拆分</li><li><button data-goto="research">查看</button>助手查询与路线推荐</li><li><button data-goto="itinerary">查看</button>逐日行程计划</li></ul><div class="dialog-actions"><button class="secondary" data-action="conditions">旅行条件</button><button class="primary" data-action="new-chat">新建对话</button></div>`;
  } else if (type === 'promotion') {
    title = '优惠信息';
    content = `<div class="dialog-copy"><p>这张界面保留了参考图中的“双11”入口。原型未接入会员或优惠活动数据。</p><p>可在“助手查询”画面查看会员权益栏目。</p></div><div class="dialog-actions"><button class="primary" data-goto="research">查看助手查询</button></div>`;
  } else if (type === 'camera') {
    title = '图片输入';
    content = `<div class="dialog-copy"><p>相机入口保留了参考图中的位置。当前静态原型以文字输入演示旅行规划流程。</p></div><div class="dialog-actions"><button class="primary" data-action="close-modal">继续输入文字</button></div>`;
  }
  host.innerHTML = `<div class="overlay" data-action="backdrop"><div class="dialog" role="dialog" aria-modal="true" aria-label="${escapeHtml(title)}"><div class="dialog-head"><h3>${escapeHtml(title)}</h3><button class="close" data-action="close-modal" aria-label="关闭">×</button></div>${content}</div></div>`;
}

function findEvent(id) {
  for (let day = 0; day < state.days.length; day++) {
    const event = state.days[day].events.find(item => item.id === id);
    if (event) return { day, event };
  }
  return null;
}

function selectRoute(index) {
  state.selectedRoute = index;
  const afternoon = findEvent('sea-1')?.event;
  if (afternoon && state.destination === '三亚') {
    afternoon.place = ROUTES[index].place;
    afternoon.title = `${ROUTES[index].place}体验`;
    afternoon.reason = index === 0 ? '三亚著名海湾，水清沙白，适宜游泳、潜水等水上活动，享受热带海滨风光' : `按照所选“${ROUTES[index].title}”安排下午活动，具体交通及开放情况待核实。`;
  }
  state.focus = 'itinerary';
  render({ top: 'itinerary' });
  showToast('已将所选路线应用到 Day 1');
}

function resetConversation() {
  state.request = '';
  state.days = sampleDays(state.destination, state.source, state.dayCount);
  state.saved.clear();
  state.selectedRoute = 0;
  state.focus = 'brief';
  state.collapsed = { thinking: false, requirements: false, destination: false, membership: false };
  state.modal = null;
  render({ top: 'brief' });
  showToast('已新建对话');
}

document.addEventListener('click', event => {
  const button = event.target.closest('button');
  if (!button) {
    if (event.target.classList.contains('overlay')) closeModal();
    return;
  }
  const data = button.dataset;
  if (data.goto) { state.focus = data.goto; state.modal = null; render(); return; }
  if (data.toggle) { state.collapsed[data.toggle] = !state.collapsed[data.toggle]; render(); return; }
  if (data.agent !== undefined) { state.activeAgent = Number(data.agent); state.focus = 'research'; render(); return; }
  if (data.route !== undefined) { selectRoute(Number(data.route)); return; }
  if (data.favorite) { state.saved.has(data.favorite) ? state.saved.delete(data.favorite) : state.saved.add(data.favorite); render(); showToast(state.saved.has(data.favorite) ? '已加入收藏' : '已取消收藏'); return; }
  if (data.editDay !== undefined) { openModal('edit-day', { day: Number(data.editDay) }); return; }
  if (data.editEvent) { openModal('edit-event', { id: data.editEvent }); return; }
  if (data.addEvent !== undefined) { openModal('add-event', { day: Number(data.addEvent) }); return; }
  if (data.action === 'jump-day') { const day = Number(data.jumpDay); state.focus = 'itinerary'; state.modal = null; render(); $(`#day-${day}`)?.scrollIntoView({ block: 'start' }); return; }
  switch (data.action) {
    case 'menu': openModal('menu'); break;
    case 'conditions': openModal('conditions'); break;
    case 'favorites': openModal('favorites'); break;
    case 'reserve': openModal('reserve'); break;
    case 'promotion': openModal('promotion'); break;
    case 'camera': openModal('camera'); break;
    case 'voice': {
      const form = button.closest('form');
      if (form?.querySelector('input[name="request"]')?.value.trim()) form.requestSubmit();
      else showToast('语音输入尚未接入；可输入文字旅行需求');
      break;
    }
    case 'sample': state.request = SAMPLE_REQUEST; parseRequest(SAMPLE_REQUEST); render({ top: 'brief' }); break;
    case 'new-chat': resetConversation(); break;
    case 'scroll-bottom': { const feed = $(`[data-feed="${data.stage}"]`); feed?.scrollTo({ top: feed.scrollHeight, behavior: 'smooth' }); break; }
    case 'close-modal': closeModal(); break;
    case 'delete-event': {
      const found = findEvent(state.modal.id);
      if (found) { state.days[found.day].events = state.days[found.day].events.filter(item => item.id !== found.event.id); state.saved.delete(found.event.id); }
      state.modal = null; render(); showToast('已删除行程安排'); break;
    }
  }
});

document.addEventListener('submit', event => {
  const form = event.target;
  event.preventDefault();
  const values = Object.fromEntries(new FormData(form));
  if (form.dataset.composer) {
    const request = values.request.trim();
    if (!request) { showToast('请先输入旅行问题'); return; }
    state.request = request;
    parseRequest(request);
    state.focus = 'brief';
    state.modal = null;
    render({ top: 'brief' });
    showToast('需求已整理，继续查看助手建议');
  } else if (form.id === 'conditions-form') {
    const source = values.source.trim(), destination = values.destination.trim(), count = Number(values.dayCount);
    const routeChanged = source !== state.source || destination !== state.destination || count !== state.dayCount;
    state.source = source; state.destination = destination; state.dayCount = count;
    state.budget = values.budget.trim() || '待补充';
    state.people = values.people.trim() || '人数待补充';
    state.preference = values.preference.trim() || '自由探索';
    if (routeChanged) { state.days = sampleDays(destination, source, count); state.saved.clear(); state.selectedRoute = 0; }
    state.modal = null; render(); showToast(routeChanged ? '已更新条件与示例行程' : '旅行条件已保存');
  } else if (form.id === 'day-form') {
    state.days[state.modal.day].title = values.title.trim();
    state.modal = null; render(); showToast('已更新当天主题');
  } else if (form.id === 'event-form') {
    const item = { kind: values.kind.trim(), title: values.title.trim(), time: values.time.trim(), place: values.place.trim(), reason: values.reason.trim() || '具体安排待确认。' };
    if (state.modal.type === 'edit-event') {
      const found = findEvent(state.modal.id);
      Object.assign(found.event, item);
      if (found.event.type === 'flight') { delete found.event.type; delete found.event.flight; }
    } else {
      item.id = `custom-${++state.customId}`;
      state.days[state.modal.day].events.push(item);
    }
    state.modal = null; render(); showToast('行程安排已保存');
  }
});

document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && state.modal) closeModal();
});

render();
