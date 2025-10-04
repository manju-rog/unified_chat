import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import api from '../../services/api';
import dataSyncService, { DATA_EVENTS } from '../../services/dataSync';
import DayDetailModal from './DayDetailModal';
import './calendar.css';

// Helper functions
const pad = (n) => (n < 10 ? '0' + n : '' + n);
const toISO = (d) => `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
const startOfMonth = (d) => new Date(d.getFullYear(), d.getMonth(), 1);
const endOfMonth = (d) => new Date(d.getFullYear(), d.getMonth()+1, 0);

// Monday start week
const weekStartIndex = 1;
const startOfGrid = (d) => {
  const day = d.getDay();
  const shift = (day - weekStartIndex + 7) % 7;
  const res = new Date(d);
  res.setDate(res.getDate() - shift);
  return res;
};

const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const weekdayShort = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];

export default function CalendarPage() {
  const [current, setCurrent] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1));
  const [department, setDepartment] = useState('');
  const [days, setDays] = useState([]);
  const [now, setNow] = useState(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Modal state
  const [modalData, setModalData] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  
  // Hover state
  const [hoveredDate, setHoveredDate] = useState(null);
  const hoverTimeoutRef = useRef(null);
  
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata';
  const locale = navigator.language || 'en-IN';
  const country = locale.toUpperCase().includes('IN') ? 'IN' : 'US';

  // Live clock
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  // Build 6-week grid
  const gridDates = useMemo(() => {
    const start = startOfGrid(startOfMonth(current));
    return Array.from({ length: 42 }, (_, i) => new Date(start.getFullYear(), start.getMonth(), start.getDate() + i));
  }, [current]);

  // Fetch calendar data
  const fetchCalendarData = useCallback(async (showLoader = false) => {
    if (showLoader) setIsRefreshing(true);
    
    const from = toISO(startOfMonth(current));
    const to = toISO(endOfMonth(current));
    try {
      const [sum, hol] = await Promise.all([
        api.calendar.getSummary({ from, to, department: department || undefined }),
        api.holidays.get({ year: current.getFullYear(), country })
      ]);
      
      // Create lookup maps
      const map = new Map();
      for (const d of sum?.days || []) map.set(d.date, d);
      const holMap = new Map((hol || []).map(h => [h.date, h]));
      
      setDays(gridDates.map(gd => {
        const iso = toISO(gd);
        const base = map.get(iso) || { date: iso, A:0, V:0, P:0, holiday:null };
        const h = holMap.get(iso);
        return { ...base, holiday: h ? { name: h.name, countryCode: h.countryCode } : base.holiday };
      }));
    } catch (e) {
      console.error('Calendar fetch failed', e);
      setDays(gridDates.map(gd => ({ date: toISO(gd), A:0, V:0, P:0, holiday: null })));
    } finally {
      if (showLoader) {
        setTimeout(() => setIsRefreshing(false), 500); // Brief delay to show the refresh
      }
    }
  }, [current, department, country, gridDates]);

  // Fetch data when month or department changes
  useEffect(() => {
    fetchCalendarData();
  }, [fetchCalendarData]);

  // Listen for real-time data changes from absence grid
  useEffect(() => {
    const unsubscribe = dataSyncService.subscribe(DATA_EVENTS.ABSENCE_DATA_SAVED, () => {
      // Refresh calendar data when absence data is saved
      console.log('Calendar: Refreshing data due to absence changes');
      fetchCalendarData(true); // Show refresh indicator
    });

    return unsubscribe;
  }, [fetchCalendarData]);

  const todayISO = toISO(new Date());
  const byISO = useMemo(() => new Map(days.map(d => [d.date, d])), [days]);
  const monthLabel = `${monthNames[current.getMonth()]} ${current.getFullYear()}`;

  // Fetch detailed day data
  const fetchDayDetails = useCallback(async (date) => {
    console.log('fetchDayDetails called with:', { date, department, country }); // Debug log
    
    // Construct the URL to see what we're actually calling
    const url = `/absences/calendar/day-details?date=${date}${department ? `&department=${encodeURIComponent(department)}` : ''}&country=${country}`;
    console.log('API URL:', `http://localhost:8080/api${url}`);
    
    try {
      const dayData = await api.calendar.getDayDetails({ 
        date, 
        department: department || undefined, 
        country 
      });
      console.log('API response:', dayData); // Debug log
      return dayData;
    } catch (error) {
      console.error('Failed to fetch day details:', error);
      console.error('Error details:', error.message);
      return null;
    }
  }, [department, country]);

  // Handle cell hover
  const handleCellHover = useCallback((date, event) => {
    console.log('Cell hovered:', date); // Debug log
    
    // Clear any existing timeout
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }

    setHoveredDate(date);

    // Store element reference for safer access during timeout
    const element = event?.currentTarget;
    if (!element) return;

    // Set timeout for 2 seconds
    hoverTimeoutRef.current = setTimeout(async () => {
      try {
        // Check if element still exists and is connected to DOM
        if (!element || !element.isConnected) {
          console.warn('Element no longer exists during hover timeout');
          return;
        }

        const rect = element.getBoundingClientRect();
        const position = {
          x: rect.left + rect.width / 2,
          y: rect.top
        };

        console.log('Hover timeout triggered for:', date); // Debug log
        const dayData = await fetchDayDetails(date);
        if (dayData) {
          setModalData(dayData);
          setIsModalOpen(true);
        } else {
          // Show fallback modal for hover too
          const fallbackData = {
            date: date,
            dayOfWeek: new Date(date).toLocaleDateString('en-US', { weekday: 'long' }).toUpperCase(),
            employees: { A: [], V: [], P: [] },
            holiday: null,
            statistics: { totalEmployees: 0, absent: 0, vacation: 0, present: 0 },
            department: department || ''
          };
          setModalData(fallbackData);
          setIsModalOpen(true);
        }
      } catch (error) {
        console.error('Error in hover handler:', error);
      }
    }, 2000);
  }, [fetchDayDetails, department]);

  // Handle cell hover leave
  const handleCellHoverLeave = useCallback(() => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    setHoveredDate(null);
  }, []);

  // Handle cell click
  const handleCellClick = useCallback(async (date, event) => {
    console.log('Cell clicked:', date); // Debug log
    
    // Clear hover timeout if exists
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }

    // Safety check: ensure event and currentTarget exist
    if (!event || !event.currentTarget) {
      console.warn('Event or currentTarget is null during click');
      return;
    }

    try {
      const rect = event.currentTarget.getBoundingClientRect();
      const position = {
        x: rect.left + rect.width / 2,
        y: rect.top
      };

      const dayData = await fetchDayDetails(date);
      
      if (dayData) {
        setModalData(dayData);
        setIsModalOpen(true);
      } else {
        // Show fallback modal with basic info
        const fallbackData = {
          date: date,
          dayOfWeek: new Date(date).toLocaleDateString('en-US', { weekday: 'long' }).toUpperCase(),
          employees: { A: [], V: [], P: [] },
          holiday: null,
          statistics: { totalEmployees: 0, absent: 0, vacation: 0, present: 0 },
          department: department || ''
        };
        setModalData(fallbackData);
        setIsModalOpen(true);
      }
    } catch (error) {
      console.error('Error in click handler:', error);
      // Show error modal
      const errorData = {
        date: date,
        dayOfWeek: new Date(date).toLocaleDateString('en-US', { weekday: 'long' }).toUpperCase(),
        employees: { A: [], V: [], P: [] },
        holiday: null,
        statistics: { totalEmployees: 0, absent: 0, vacation: 0, present: 0 },
        department: department || '',
        error: 'Failed to load data'
      };
      setModalData(errorData);
      setIsModalOpen(true);
    }
  }, [fetchDayDetails, department]);

  // Close modal
  const closeModal = useCallback(() => {
    setIsModalOpen(false);
    setModalData(null);
  }, []);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="cal-shell">
      <header className="cal-topbar">
        <div className="cal-left">
          <button 
            className="navbtn" 
            onClick={()=>setCurrent(new Date(current.getFullYear(), current.getMonth()-1, 1))}
            aria-label="Previous month"
          >
            ‹
          </button>
          <div className="month">{monthLabel}</div>
          <button 
            className="navbtn" 
            onClick={()=>setCurrent(new Date(current.getFullYear(), current.getMonth()+1, 1))}
            aria-label="Next month"
          >
            ›
          </button>
          <button 
            className="todaybtn" 
            onClick={()=>{
              const n=new Date(); 
              setCurrent(new Date(n.getFullYear(), n.getMonth(), 1));
            }}
          >
            Today
          </button>
        </div>
        <div className="cal-right">
          {isRefreshing && (
            <div className="refresh-indicator">
              <div className="refresh-spinner"></div>
              <span>Syncing...</span>
            </div>
          )}
          <select className="dept" value={department} onChange={e=>setDepartment(e.target.value)}>
            <option value="">All Departments</option>
            <option>Engineering</option>
            <option>Marketing</option>
            <option>HR</option>
            <option>Operations</option>
          </select>
          <div className="tz">
            <div className="dot" />
            <div className="tzline">
              <div className="tzname">{tz}</div>
              <div className="clock">
                {now.toLocaleTimeString([], { hour: '2-digit', minute:'2-digit', second:'2-digit' })}
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="cal-head">
        {weekdayShort.map((w, i) => <div key={i} className="wcell">{w}</div>)}
      </div>

      <div className="cal-grid">
        {gridDates.map((d) => {
          const iso = toISO(d);
          const inMonth = d.getMonth() === current.getMonth();
          const info = byISO.get(iso);
          const isWeekend = [0,6].includes(d.getDay());
          const isToday = iso === todayISO;
          const isHovered = hoveredDate === iso;
          
          return (
            <div 
              key={iso} 
              className={`cell ${inMonth ? '' : 'dim'} ${isWeekend ? 'weekend':''} ${isToday ? 'today':''} ${isHovered ? 'hovered' : ''}`}
              onMouseEnter={(e) => handleCellHover(iso, e)}
              onMouseLeave={handleCellHoverLeave}
              onClick={(e) => handleCellClick(iso, e)}
            >
              <div className="cell-top">
                <div className="date">{d.getDate()}</div>
                {info?.holiday?.name ? 
                  <div className="chip chip-holiday" title={info.holiday.name}>
                    {info.holiday.name}
                  </div> : null
                }
              </div>
              <div className="bar">
                <Badge label="A" value={info?.A||0} />
                <Badge label="V" value={info?.V||0} />
                <Badge label="P" value={info?.P||0} />
              </div>
              {isHovered && (
                <div className="hover-indicator">
                  <span>Click for details</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <footer className="cal-legend">
        <span className="legend"><b className="b bA" /> Absent</span>
        <span className="legend"><b className="b bV" /> Vacation</span>
        <span className="legend"><b className="b bP" /> Present</span>
        <span className="legend"><b className="b bH" /> Public Holiday</span>
        <span className="legend-tip">💡 Hover for 2s or click any date for details</span>
        <button 
          onClick={() => {
            console.log('Test button clicked');
            setModalData({
              date: '2024-08-29',
              dayOfWeek: 'THURSDAY',
              employees: { A: [], V: [], P: [{ id: 1, name: 'Test User', email: 'test@test.com', department: 'Engineering' }] },
              holiday: null,
              statistics: { totalEmployees: 1, absent: 0, vacation: 0, present: 1 }
            });
            setIsModalOpen(true);
          }}
          style={{ marginLeft: '10px', padding: '5px 10px', background: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}
        >
          Test Modal
        </button>
        <button 
          onClick={async () => {
            try {
              const employees = await api.employees.getAll();
              console.log('Employees in database:', employees);
              alert(`Found ${employees.length} employees in database`);
            } catch (error) {
              console.error('Failed to fetch employees:', error);
              alert('Failed to fetch employees: ' + error.message);
            }
          }}
          style={{ marginLeft: '10px', padding: '5px 10px', background: '#28a745', color: 'white', border: 'none', borderRadius: '4px' }}
        >
          Check Employees
        </button>
      </footer>

      {/* Day Detail Modal */}
      <DayDetailModal
        dayData={modalData}
        isOpen={isModalOpen}
        onClose={closeModal}
      />
    </div>
  );
}

function Badge({ label, value }) {
  if (!value) return <span className="badge empty">{label}: 0</span>;
  return <span className={`badge b-${label}`}>{label}: {value}</span>;
}