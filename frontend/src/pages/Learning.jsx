import { useState, useEffect } from "react";
import { useApp } from "../contexts/AppContext";
import { learningAPI, podcastAPI } from "../services/api";
import CandleLoader from "../components/ui/CandleLoader";

export default function Learning({ userId }) {
  const { language } = useApp();
  const [modules, setModules] = useState([]);
  const [selectedLesson, setSelectedLesson] = useState(null);
  const [lessonContent, setLessonContent] = useState(null);
  const [scenario, setScenario] = useState(null);
  const [scenarioFeedback, setScenarioFeedback] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lessonLoading, setLessonLoading] = useState(false);
  const [error, setError] = useState("");
  const [view, setView] = useState("modules"); // "modules" | "lessons" | "lesson"
  const [expandedModule, setExpandedModule] = useState(null); // {module_id, title, lessons[]}
  const [moduleLessonsLoading, setModuleLessonsLoading] = useState(false);
  const [podcastData, setPodcastData] = useState(null); // {audio_url, podcast_script, ...}
  const [podcastLoading, setPodcastLoading] = useState(false);

  useEffect(() => { if (userId) loadModules(); }, [userId, language]);

  const loadModules = async () => {
    setLoading(true);
    try {
      const res = await learningAPI.getModules(userId, language);
      // pillars comes as { savings: [...], credit: [...] } — convert to array
      const pillarsData = res.pillars || res.modules || [];
      if (pillarsData && !Array.isArray(pillarsData) && typeof pillarsData === 'object') {
        const arr = Object.entries(pillarsData).map(([key, mods]) => ({
          pillar: key,
          modules: mods,
        }));
        setModules(arr);
      } else {
        setModules(Array.isArray(pillarsData) ? pillarsData : []);
      }
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  const openModule = async (moduleId, moduleTitle) => {
    setModuleLessonsLoading(true);
    setError('');
    try {
      const res = await learningAPI.getModuleLessons(moduleId, userId, language);
      setExpandedModule({
        module_id: moduleId,
        title: res.title || moduleTitle,
        pillar: res.pillar,
        level: res.level,
        lessons: res.lessons || [],
      });
      setView('lessons');
    } catch (e) { setError(e.message); }
    setModuleLessonsLoading(false);
  };

  const openLesson = async (lessonId) => {
    setLessonLoading(true);
    setScenario(null);
    setScenarioFeedback(null);
    setPodcastData(null);
    try {
      const res = await learningAPI.getLessonContent(lessonId, userId, language);
      setLessonContent(res);
      setSelectedLesson(lessonId);
      setView("lesson");
      // Load existing podcasts for this lesson
      try {
        const pods = await podcastAPI.getLessonPodcasts(lessonId);
        if (pods.available_podcasts?.length > 0) {
          setPodcastData(pods.available_podcasts);
        }
      } catch (_) { /* no podcasts yet */ }
    } catch (e) { setError(e.message); }
    setLessonLoading(false);
  };

  const loadScenario = async () => {
    // Scenario is already embedded in the lesson response
    if (lessonContent?.scenario) {
      setScenario(lessonContent.scenario);
    } else {
      setError(language === 'hi' ? 'कोई परिदृश्य उपलब्ध नहीं' : 'No scenario available for this lesson');
    }
  };

  const answerScenario = async (optionIdx) => {
    try {
      const res = await learningAPI.answerScenario(selectedLesson, userId, optionIdx);
      setScenarioFeedback(res);
    } catch (e) { setError(e.message); }
  };

  const completeLesson = async () => {
    try {
      await learningAPI.completeLesson(selectedLesson, userId, false);
      // Go back to module lessons if we came from there
      if (expandedModule) {
        await openModule(expandedModule.module_id, expandedModule.title);
      } else {
        setView("modules");
        setSelectedLesson(null);
        loadModules();
      }
    } catch (e) { setError(e.message); }
  };

  const generatePodcast = async (lessonId) => {
    setPodcastLoading(true);
    try {
      const res = await podcastAPI.generatePodcast(lessonId, language);
      // Refresh podcast list
      const pods = await podcastAPI.getLessonPodcasts(lessonId);
      if (pods.available_podcasts?.length > 0) {
        setPodcastData(pods.available_podcasts);
      } else if (res.audio_url) {
        setPodcastData([res]);
      }
    } catch (e) { alert(e.message); }
    setPodcastLoading(false);
  };

  // Lesson detail view
  if (view === "lesson" && lessonContent) {
    return (
      <div style={{ padding: '1rem' }}>
        <button onClick={() => {
          if (expandedModule) { setView('lessons'); }
          else { setView('modules'); }
          setSelectedLesson(null);
          setLessonContent(null);
          setScenario(null);
          setScenarioFeedback(null);
          setPodcastData(null);
        }}
          style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', cursor: 'pointer', fontSize: '0.9rem', marginBottom: '1rem' }}>
          ← {language === 'hi' ? 'वापस जाएं' : 'Back'}
        </button>

        <div style={{ background: 'var(--card-bg)', borderRadius: '16px', padding: '1.5rem', border: '1px solid var(--border-subtle)' }}>
          <h2 style={{ marginBottom: '0.5rem' }}>{lessonContent.title || 'Lesson'}</h2>
          {lessonContent.pillar && <span style={{ background: 'var(--accent-primary)', color: '#fff', padding: '2px 10px', borderRadius: '12px', fontSize: '0.75rem' }}>{lessonContent.pillar}</span>}

          {/* Main content (story) */}
          <div style={{ marginTop: '1.5rem', lineHeight: 1.8, whiteSpace: 'pre-wrap', fontSize: '0.95rem' }}>
            {lessonContent.story || lessonContent.original_story || lessonContent.content || (language === 'hi' ? 'सामग्री लोड हो रही है...' : 'Loading content...')}
          </div>

          {/* Key takeaway */}
          {lessonContent.takeaway && (
            <div style={{ marginTop: '1.5rem', background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1rem' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>💡 {language === 'hi' ? 'मुख्य बातें' : 'Key Takeaway'}</h3>
              <p style={{ lineHeight: 1.8 }}>{lessonContent.takeaway}</p>
            </div>
          )}

          {/* Tool suggestion */}
          {lessonContent.tool_suggestion && (
            <div style={{ marginTop: '1rem', background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1rem' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>🛠️ {language === 'hi' ? 'सुझाया गया टूल' : 'Suggested Tool'}</h3>
              <p style={{ lineHeight: 1.8 }}>{lessonContent.tool_suggestion}</p>
            </div>
          )}

          {/* XP reward */}
          {lessonContent.xp_reward && (
            <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
              🌟 +{lessonContent.xp_reward} XP
            </div>
          )}

          {/* Scenario question */}
          {!scenario && !scenarioFeedback && (
            <button onClick={loadScenario} style={{ marginTop: '1.5rem', padding: '0.7rem 1.5rem', background: 'var(--accent-primary)', color: '#fff', border: 'none', borderRadius: '10px', cursor: 'pointer', fontSize: '0.9rem' }}>
              🧩 {language === 'hi' ? 'परिदृश्य प्रश्न हल करें' : 'Try Scenario Question'}
            </button>
          )}

          {scenario && !scenarioFeedback && (
            <div style={{ marginTop: '1.5rem', background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1.25rem' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>🧩 {scenario.question}</h3>
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                {(scenario.options || []).map((opt, i) => (
                  <button key={i} onClick={() => answerScenario(i)}
                    style={{ padding: '0.7rem 1rem', background: 'var(--card-bg)', border: '1px solid var(--border-subtle)', borderRadius: '10px', cursor: 'pointer', textAlign: 'left', color: 'var(--text-primary)' }}>
                    {typeof opt === 'string' ? opt : opt.text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {scenarioFeedback && (
            <div style={{ marginTop: '1rem', padding: '1rem', borderRadius: '12px',
              background: scenarioFeedback.is_correct ? 'rgba(46,204,113,0.1)' : 'rgba(231,76,60,0.1)',
              border: `1px solid ${scenarioFeedback.is_correct ? '#2ecc71' : '#e74c3c'}` }}>
              <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>
                {scenarioFeedback.is_correct ? '✅' : '❌'} {scenarioFeedback.explanation || (scenarioFeedback.is_correct ? 'Correct!' : 'Incorrect')}
              </p>
              {scenarioFeedback.health_impact && (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Health Impact: {scenarioFeedback.health_impact > 0 ? '+' : ''}{scenarioFeedback.health_impact}
                </p>
              )}
            </div>
          )}

          {/* Podcast Player */}
          {podcastData && podcastData.length > 0 && (
            <div style={{ marginTop: '1.5rem', background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1.25rem' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>🎧 {language === 'hi' ? 'पॉडकास्ट सुनें' : 'Listen to Podcast'}</h3>
              {podcastData.map((pod) => (
                <div key={pod.podcast_id || pod.language} style={{ marginBottom: '0.75rem' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                    {pod.language_name || pod.language?.toUpperCase()}
                    {pod.duration_seconds ? ` · ${Math.round(pod.duration_seconds / 60)}m ${Math.round(pod.duration_seconds % 60)}s` : ''}
                    {pod.speakers ? ` · ${pod.speakers.host} & ${pod.speakers.cohost}` : ''}
                  </p>
                  <audio controls preload="none" style={{ width: '100%', borderRadius: '8px' }}
                    src={pod.audio_url}>
                    Your browser does not support audio.
                  </audio>
                </div>
              ))}
            </div>
          )}

          {/* Complete & Podcast */}
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem', flexWrap: 'wrap' }}>
            <button onClick={completeLesson}
              style={{ padding: '0.7rem 1.5rem', background: '#2ecc71', color: '#fff', border: 'none', borderRadius: '10px', cursor: 'pointer', fontSize: '0.9rem' }}>
              ✓ {language === 'hi' ? 'पाठ पूर्ण करें' : 'Complete Lesson'}
            </button>
            <button onClick={() => generatePodcast(selectedLesson)} disabled={podcastLoading}
              style={{ padding: '0.7rem 1.5rem', background: podcastLoading ? '#999' : 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '10px', cursor: podcastLoading ? 'wait' : 'pointer', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
              🎧 {podcastLoading ? (language === 'hi' ? 'बन रहा है...' : 'Generating...') : (language === 'hi' ? 'पॉडकास्ट बनाएं' : 'Generate Podcast')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Module Lessons View ──
  if (view === 'lessons' && expandedModule) {
    return (
      <div style={{ padding: '1rem' }}>
        <button onClick={() => { setView('modules'); setExpandedModule(null); loadModules(); }}
          style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', cursor: 'pointer', fontSize: '0.9rem', marginBottom: '1rem' }}>
          ← {language === 'hi' ? 'सभी मॉड्यूल' : 'All Modules'}
        </button>

        <div style={{ marginBottom: '1.25rem' }}>
          <h1 style={{ fontSize: '1.3rem', marginBottom: '0.25rem' }}>
            {expandedModule.title}
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            {expandedModule.pillar && <span style={{ textTransform: 'capitalize' }}>{expandedModule.pillar}</span>}
            {expandedModule.level && <span> · {expandedModule.level}</span>}
            {' · '}{expandedModule.lessons.length} {language === 'hi' ? 'पाठ' : 'lessons'}
          </p>
        </div>

        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {expandedModule.lessons.map((lesson, i) => (
            <div key={lesson.lesson_id || i}
              onClick={() => !lesson.locked && openLesson(lesson.lesson_id || lesson.id)}
              style={{
                background: 'var(--card-bg)', borderRadius: '14px', padding: '1rem 1.25rem',
                border: `1px solid ${lesson.completed ? '#2ecc71' : 'var(--border-subtle)'}`,
                cursor: lesson.locked ? 'not-allowed' : 'pointer',
                opacity: lesson.locked ? 0.5 : 1,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                transition: 'border-color 0.2s',
              }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <span style={{ fontSize: '1.1rem' }}>
                    {lesson.completed ? '✅' : lesson.locked ? '🔒' : '📖'}
                  </span>
                  <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{lesson.title}</span>
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  {lesson.xp_reward > 0 && <span>⭐ {lesson.xp_reward} XP</span>}
                  {lesson.has_scenario && <span>🧩 Scenario</span>}
                  {lesson.has_podcast && <span>🎧 Podcast</span>}
                  {lesson.has_tool && <span>🔧 {lesson.tool_name || 'Tool'}</span>}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {lesson.scenario_correct === true && <span style={{ color: '#2ecc71', fontSize: '0.8rem' }}>🎯</span>}
                {lesson.scenario_correct === false && <span style={{ color: '#e74c3c', fontSize: '0.8rem' }}>✗</span>}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" strokeWidth="2">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              </div>
            </div>
          ))}
        </div>

        {expandedModule.lessons.length === 0 && (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
            {language === 'hi' ? 'इस मॉड्यूल में कोई पाठ नहीं' : 'No lessons in this module'}
          </div>
        )}
      </div>
    );
  }

  // Module list view
  return (
    <div style={{ padding: '1rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>
          📚 {language === 'hi' ? 'सीखने की यात्रा' : 'Learning Journey'}
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          {language === 'hi' ? '4 स्तंभ × 3 स्तर — व्यक्तिगत वित्तीय शिक्षा' : '4 Pillars × 3 Levels — Personalized Financial Education'}
        </p>
      </div>

      {error && <p style={{ color: '#e74c3c', marginBottom: '1rem' }}>{error}</p>}

      {loading ? (
        <CandleLoader message={language === 'hi' ? 'मॉड्यूल लोड हो रहे हैं...' : 'Loading modules...'} />
      ) : (
        <div style={{ display: 'grid', gap: '1.25rem' }}>
          {modules.map((pillar, pIdx) => (
            <div key={pIdx} style={{ background: 'var(--card-bg)', borderRadius: '16px', padding: '1.25rem', border: '1px solid var(--border-subtle)' }}>
              <h2 style={{ fontSize: '1.1rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {pillar.pillar === 'savings' ? '💰' : pillar.pillar === 'credit' ? '💳' : pillar.pillar === 'investments' ? '📈' : pillar.pillar === 'small_business' ? '🏪' : '🛡️'}
                <span style={{ textTransform: 'capitalize' }}>{(pillar.pillar || pillar.name || '').replace(/_/g, ' ')}</span>
                {pillar.locked && <span style={{ fontSize: '0.7rem', background: '#e74c3c', color: '#fff', padding: '2px 8px', borderRadius: '8px' }}>🔒</span>}
              </h2>

              <div style={{ display: 'grid', gap: '0.5rem' }}>
                {(pillar.modules || pillar.lessons || []).map((mod, mIdx) => (
                  <div key={mIdx} style={{ background: 'var(--bg-secondary)', borderRadius: '12px', padding: '0.75rem 1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{mod.title || mod.name}</span>
                        {mod.level && <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>({mod.level})</span>}
                        {mod.description && <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>{mod.description}</div>}
                        {mod.lock_reason && <div style={{ fontSize: '0.7rem', color: '#e74c3c', marginTop: '0.15rem' }}>🔒 {mod.lock_reason}</div>}
                      </div>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        {mod.completed_lessons > 0 && mod.completed_lessons >= mod.total_lessons && <span style={{ color: '#2ecc71', fontSize: '0.85rem' }}>✓</span>}
                        <button onClick={() => openModule(mod.module_id || mod.id, mod.title || mod.name)}
                          disabled={mod.is_locked || mod.locked}
                          style={{ padding: '0.3rem 0.75rem', fontSize: '0.75rem', background: mod.completed_lessons > 0 && mod.completed_lessons >= mod.total_lessons ? '#2ecc71' : 'var(--accent-primary)', color: '#fff', border: 'none', borderRadius: '8px', cursor: (mod.is_locked || mod.locked) ? 'not-allowed' : 'pointer', opacity: (mod.is_locked || mod.locked) ? 0.5 : 1 }}>
                          {mod.completed_lessons > 0 ? `${mod.completed_lessons}/${mod.total_lessons}` : (language === 'hi' ? 'शुरू करें' : 'Start')}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {modules.length === 0 && (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
              {language === 'hi' ? 'कोई मॉड्यूल उपलब्ध नहीं। कृपया पहले मूल्यांकन पूरा करें।' : 'No modules available. Please complete the assessment first.'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

