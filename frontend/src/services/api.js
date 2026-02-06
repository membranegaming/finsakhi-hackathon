/**
 * FinSakhi API Service — Real Backend Integration
 * All endpoints proxy through Vite dev server to http://localhost:8000
 */

const API_BASE = '/api';

// ─── Helpers ───────────────────────────────────────────────
async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  } catch (e) {
    console.error(`API ${options.method || 'GET'} ${url} failed:`, e.message);
    throw e;
  }
}
function get(path) { return request(path); }
function post(path, body) { return request(path, { method: 'POST', body: JSON.stringify(body) }); }
function del(path) { return request(path, { method: 'DELETE' }); }

// ─── Auth (OTP-based) ─────────────────────────────────────
export const authAPI = {
  sendOTP: (phone, language = 'en') =>
    post('/auth/send-otp', { phone, language }),

  verifyOTP: (phone, otp, name = null) =>
    post('/auth/verify-otp', { phone, otp, name }),

  getProfile: (userId) =>
    get(`/auth/me?user_id=${userId}`),
};

// ─── Assessment (Profile + Adaptive MCQ) ──────────────────
export const assessmentAPI = {
  start: (userId, language = 'en') =>
    post('/assessment/start', { user_id: userId, language }),

  answerProfile: (sessionId, answer) =>
    post('/assessment/answer-profile', { session_id: sessionId, answer }),

  answerMCQ: (sessionId, selectedOption) =>
    post('/assessment/answer-mcq', { session_id: sessionId, selected_option: selectedOption }),

  getResult: (sessionId) =>
    get(`/assessment/result/${sessionId}`),

  getHistory: (userId) =>
    get(`/assessment/user-history/${userId}`),
};

// ─── Learning ─────────────────────────────────────────────
export const learningAPI = {
  getModules: (userId, language = 'en') =>
    get(`/learning/modules/${userId}?language=${language}`),

  getModuleLessons: (moduleId, userId, language = 'en') =>
    get(`/learning/module/${moduleId}/lessons?user_id=${userId}&language=${language}`),

  getLessonContent: (lessonId, userId, language = 'en') =>
    get(`/learning/lesson/${lessonId}?user_id=${userId}&language=${language}`),

  answerScenario: (lessonId, userId, selectedOption) =>
    post(`/learning/lesson/${lessonId}/scenario`, { user_id: userId, selected_option: selectedOption }),

  completeLesson: (lessonId, userId, toolUsed = false) =>
    post(`/learning/lesson/${lessonId}/complete`, { user_id: userId, tool_used: toolUsed }),

  getProgress: (userId, language = 'en') =>
    get(`/learning/progress/${userId}?language=${language}`),

  getHealth: (userId) =>
    get(`/learning/health/${userId}`),

  getNextLesson: (userId, language = 'en') =>
    get(`/learning/next/${userId}?language=${language}`),
};

// ─── Investments ──────────────────────────────────────────
export const investmentAPI = {
  getCommodities: () =>
    get('/investments/commodities'),

  getCommodity: (commodity) =>
    get(`/investments/commodities/${commodity}`),

  getCommodityHistory: (commodity, period = '1mo') =>
    get(`/investments/commodities/${commodity}/history?period=${period}`),

  getPopularMutualFunds: () =>
    get('/investments/mutual-funds/popular'),

  searchMutualFunds: (query) =>
    get(`/investments/mutual-funds/search?q=${encodeURIComponent(query)}`),

  getMutualFundNav: (schemeCode) =>
    get(`/investments/mutual-funds/${schemeCode}`),

  getMutualFundHistory: (schemeCode, days = 30) =>
    get(`/investments/mutual-funds/${schemeCode}/history?days=${days}`),
};

// ─── Portfolio (Virtual Trading) ──────────────────────────
export const portfolioAPI = {
  getPortfolio: (userId) =>
    get(`/portfolio/${userId}`),

  buy: (userId, assetType, assetSymbol, assetName, quantity, language = 'en') =>
    post('/portfolio/buy', { user_id: userId, asset_type: assetType, asset_symbol: assetSymbol, asset_name: assetName, quantity, language }),

  sell: (userId, investmentId, quantity, language = 'en') =>
    post('/portfolio/sell', { user_id: userId, investment_id: investmentId, quantity, language }),
};

// ─── Goals ────────────────────────────────────────────────
export const goalsAPI = {
  getGoals: (userId) =>
    get(`/goals/${userId}`),

  createGoal: (userId, title, targetAmount, category = 'savings', deadline = null, language = 'en') =>
    post('/goals/create', { user_id: userId, title, target_amount: targetAmount, category, deadline, language }),

  updateGoal: (goalId, userId, updates = {}) =>
    request(`/goals/${goalId}`, { method: 'PUT', body: JSON.stringify({ user_id: userId, ...updates }) }),

  deleteGoal: (goalId, userId) =>
    del(`/goals/${goalId}?user_id=${userId}`),
};

// ─── Chatbot ──────────────────────────────────────────────
export const chatAPI = {
  sendMessage: (userId, message, conversationId = null, language = 'en') =>
    post('/chat/send', { user_id: userId, message, conversation_id: conversationId, language }),

  getConversations: (userId) =>
    get(`/chat/conversations/${userId}`),

  getConversationMessages: (userId, conversationId) =>
    get(`/chat/conversations/${userId}/${conversationId}`),

  deleteConversation: (userId, conversationId) =>
    del(`/chat/conversations/${userId}/${conversationId}`),
};

// ─── Recommendations (Credit Cards + Govt Schemes) ───────
export const recommendationsAPI = {
  getCreditCards: (userId, language = 'en') =>
    post('/recommendations/credit-cards', { user_id: userId, language }),

  getGovtSchemes: (userId, language = 'en') =>
    post('/recommendations/govt-schemes', { user_id: userId, language }),

  getAllSchemes: () =>
    get('/recommendations/schemes/all'),

  getAllCards: () =>
    get('/recommendations/cards/all'),
};

// ─── Podcasts ─────────────────────────────────────────────
export const podcastAPI = {
  generatePodcast: (lessonId, language = 'en') =>
    post('/podcasts/generate', { lesson_id: lessonId, language }),

  getLessonPodcasts: (lessonId) =>
    get(`/podcasts/lesson/${lessonId}`),

  getAudioUrl: (podcastId) =>
    `/api/podcasts/audio/${podcastId}`,

  getScript: (podcastId) =>
    get(`/podcasts/script/${podcastId}`),

  getSupportedLanguages: () =>
    get('/podcasts/languages'),
};

export default {
  auth: authAPI,
  assessment: assessmentAPI,
  learning: learningAPI,
  investment: investmentAPI,
  portfolio: portfolioAPI,
  goals: goalsAPI,
  chat: chatAPI,
  recommendations: recommendationsAPI,
  podcast: podcastAPI,
};

