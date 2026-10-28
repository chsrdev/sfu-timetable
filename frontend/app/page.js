'use client';

import { useEffect, useMemo, useRef, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

function normalize(value) {
  return value.toLocaleLowerCase('ru').replace(/[\s\-_/\\]/g, '');
}

export default function Home() {
  const [groups, setGroups] = useState([]);
  const [institute, setInstitute] = useState('');
  const [groupName, setGroupName] = useState('');
  const [subgroup, setSubgroup] = useState('');
  const [isSuggestionsOpen, setSuggestionsOpen] = useState(false);
  const [calendarUrl, setCalendarUrl] = useState('');
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');
  const suggestionsRef = useRef(null);

  useEffect(() => {
    fetch(`${API_URL}/api/groups`)
      .then((response) => {
        if (!response.ok) throw new Error('Не удалось загрузить список групп');
        return response.json();
      })
      .then(setGroups)
      .catch((reason) => setError(reason.message));
  }, []);

  useEffect(() => {
    function closeSuggestions(event) {
      if (!suggestionsRef.current?.contains(event.target)) setSuggestionsOpen(false);
    }
    document.addEventListener('mousedown', closeSuggestions);
    return () => document.removeEventListener('mousedown', closeSuggestions);
  }, []);

  const institutes = useMemo(
    () => [...new Set(groups.map((group) => group.institute).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'ru')),
    [groups]
  );

  const suggestions = useMemo(() => {
    const search = normalize(groupName);
    return groups
      .filter((group) => !institute || group.institute === institute)
      .filter((group) => !search || normalize(group.name).includes(search))
      .slice(0, 8);
  }, [groups, groupName, institute]);

  const selectedGroup = groups.find(
    (group) => group.name === groupName && (!institute || group.institute === institute)
  );
  const hasSubgroups = Boolean(selectedGroup?.subgroups?.length);

  function selectInstitute(value) {
    setInstitute(value);
    setGroupName('');
    setSubgroup('');
    setCalendarUrl('');
    setSuggestionsOpen(false);
  }

  function selectGroup(group) {
    setGroupName(group.name);
    setSubgroup(group.subgroups?.[0] || '');
    setCalendarUrl('');
    setSuggestionsOpen(false);
  }

  function changeGroup(value) {
    setGroupName(value);
    setSubgroup('');
    setCalendarUrl('');
    setSuggestionsOpen(true);
  }

  async function createLink(event) {
    event.preventDefault();
    setError('');
    setCopied(false);
    const fullName = hasSubgroups ? `${groupName} (${subgroup} подгруппа)` : groupName;
    try {
      const response = await fetch(`${API_URL}/api/calendar-link?group=${encodeURIComponent(fullName)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Не удалось создать ссылку');
      setCalendarUrl(data.url);
    } catch (reason) {
      setError(reason.message);
    }
  }

  async function copyLink() {
    await navigator.clipboard.writeText(calendarUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <main className="page-shell">
      <nav className="nav"><div className="brand"><span className="brand-mark">S</span> sfu<span>calendar</span></div><div className="nav-caption">Расписание всегда под рукой</div></nav>
      <section className="hero">
        <div className="eyebrow">CALENDAR FOR SFU</div>
        <h1>Твоё расписание.<br /><em>Всегда актуальное.</em></h1>
        <p className="lead">Выбери институт, группу и подпишись на календарь. Новые занятия появятся в телефоне автоматически.</p>
        <form className="card" onSubmit={createLink}>
          <label htmlFor="institute">Институт</label>
          <select id="institute" value={institute} onChange={(event) => selectInstitute(event.target.value)} required>
            <option value="">Выбери институт</option>
            {institutes.map((item) => <option value={item} key={item}>{item}</option>)}
          </select>

          <label htmlFor="group">Группа</label>
          <div className="combobox" ref={suggestionsRef}>
            <input
              id="group"
              value={groupName}
              onChange={(event) => changeGroup(event.target.value)}
              onFocus={() => setSuggestionsOpen(true)}
              placeholder={institute ? 'Начни вводить группу…' : 'Сначала выбери институт'}
              disabled={!institute}
              autoComplete="off"
              required
            />
            {isSuggestionsOpen && institute && suggestions.length > 0 && (
              <div className="suggestions" role="listbox">
                {suggestions.map((group) => (
                  <button type="button" className="suggestion" key={group.name} onClick={() => selectGroup(group)}>
                    <span>{group.name}</span><small>{group.course} курс</small>
                  </button>
                ))}
              </div>
            )}
          </div>

          {hasSubgroups && <div className="subgroup-row"><div><label htmlFor="subgroup">Подгруппа</label><select id="subgroup" value={subgroup} onChange={(event) => setSubgroup(event.target.value)} required>{selectedGroup.subgroups.map((item) => <option value={item} key={item}>{item} подгруппа</option>)}</select></div><button type="submit" disabled={!selectedGroup}>Создать календарь <span>→</span></button></div>}
          {!hasSubgroups && <button className="full-button" type="submit" disabled={!selectedGroup}>Создать календарь <span>→</span></button>}
        </form>
        {calendarUrl && <div className="result"><div><div className="result-title">Календарь готов</div><div className="result-text">Скопируй ссылку и добавь её как подписной календарь.</div><code>{calendarUrl}</code></div><button className="copy" onClick={copyLink}>{copied ? 'Скопировано ✓' : 'Копировать'}</button></div>}
        {error && <p className="error">{error}</p>}
      </section>
      <footer><span>Apple Calendar</span><span>Google Calendar</span><span>Outlook</span></footer>
    </main>
  );
}
