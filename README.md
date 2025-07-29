# Kung Fu Chess - Client/Server Architecture

מימוש מלא של משחק Kung Fu Chess עם ארכיטקטורת Client/Server באמצעות WebSockets.

## מבנה הפרויקט

```
├── server/                     # שרת המשחק
│   ├── kungfu_chess/          # מנוע המשחק ו-API
│   │   ├── engine.py          # מנוע השחמט
│   │   ├── bus.py             # מערכת אירועים
│   │   ├── command_queue.py   # תור פקודות
│   │   └── api_ws.py          # WebSocket API
│   ├── main.py                # נקודת כניסה לשרת
│   └── requirements.txt       # תלויות השרת
├── client/                     # קליינטים
│   ├── ui/                    # רכיבי ממשק משתמש
│   │   ├── board_widget.py    # לוח השחמט הגרפי
│   │   └── assets/            # תמונות הכלים
│   ├── network.py             # תקשורת WebSocket
│   ├── white_client.py        # קליינט שחקן לבן
│   ├── black_client.py        # קליינט שחקן שחור
│   └── requirements.txt       # תלויות הקליינט
└── tests/                      # בדיקות
```

## התקנה והפעלה

### הפעלת השרת

```bash
cd server
pip install -r requirements.txt
python main.py
```

השרת יפעל על `http://localhost:8000`

### הפעלת הקליינטים

#### טרמינל ראשון - קליינט לבן:
```bash
cd client
pip install -r requirements.txt
python white_client.py
```

#### טרמינל שני - קליינט שחור:
```bash
cd client
python black_client.py
```

## אופן המשחק

1. **התחברות**: כל קליינט מתחבר אוטומטית לשרת
2. **הקצאת צבעים**: השחקן הראשון יקבל לבן, השני שחור
3. **משחק**: גרור ושחרר כלים על הלוח לביצוע מהלכים
4. **עדכונים**: כל המהלכים מתעדכנים בזמן אמת בשני הקליינטים

## תכונות עיקריות

- ☑️ שרת WebSocket עם FastAPI
- ☑️ מנוע שחמט מותאם ל-Kung Fu Chess
- ☑️ ממשק גרפי עם PySide6
- ☑️ Drag & Drop לביצוע מהלכים
- ☑️ עדכון בזמן אמת
- ☑️ טיפול בשגיאות
- ☑️ לוחות נפרדים לכל שחקן

## פרוטוקול התקשורת

### Client → Server
```json
{"type": "command", "pgn": "Qe2e5"}
```

### Server → Client
```json
{"type": "execute", "pgn": "Qe2e5", "board": {...}}
{"type": "error", "message": "illegal move"}
{"type": "game_over", "winner": "White"}
```

## בדיקת תקינות

נתיב בדיקה: `GET http://localhost:8000/healthz`

## דרישות מערכת

- Python 3.8+
- מערכת הפעלה עם תמיכה ב-GUI (Linux/Windows/macOS)
- רשת מקומית או localhost

## פתרון בעיות

### בעיות התחברות
- ודא שהשרת פועל לפני הפעלת הקליינטים
- בדוק שפורט 8000 פנוי

### בעיות GUI
- ודא שהותקנה PySide6 בצורה תקינה
- בדוק שיש גישה למערכת חלונות

### בעיות תמונות
- ודא שתיקיית assets מכילה את תמונות הכלים