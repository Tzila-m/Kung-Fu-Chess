# 🎮 Kung Fu Chess - Client/Server Edition

ארכיטקטורת Client/Server מלאה למשחק שחמט Kung Fu, מבוססת על המנוע הקיים במשחק המקורי.

## 🎯 תיאור המשחק

משחק שחמט Kung Fu הוא וריאציה מהירה ומרגשת של שחמט קלאסי, שבו כל השחקנים יכולים להזיז כלים בו-זמנית ללא תורות קבועים. המטרה היא להשמיד את המלך של היריב.

## 🏗️ ארכיטקטורה

המערכת מורכבת משלושה רכיבים עיקריים:

### 🖥️ Server (`server/`)
- **מנוע המשחק**: מתבסס על הקוד המקורי מ-`CTD25_Solutions`
- **WebSocket API**: תקשורת בזמן אמת עם הקליינטים
- **תור פקודות**: עיבוד פקודות משחק בצורה מסודרת
- **מנהל חיבורים**: ניהול שני קליינטים מקסימום

### 🎮 Client (`client/`)
- **GUI עם Tkinter**: ממשק גרפי לוח שחמט
- **WebSocket Client**: תקשורת עם השרת
- **שני אפליקציות**: קליינט לבן וקליינט שחור

### 📁 מבנה הפרויקט
```
├── server/
│   ├── kungfu_chess/          # מנוע המשחק המותאם
│   │   ├── game_server.py     # עטיפת השרת למשחק
│   │   ├── Game.py            # מנוע המשחק הקיים
│   │   ├── Board.py           # לוח המשחק
│   │   ├── Piece.py           # כלי השחמט
│   │   ├── Command.py         # פקודות משחק
│   │   ├── Physics.py         # פיזיקת המשחק
│   │   ├── Graphics.py        # גרפיקה
│   │   └── ...               # קבצים נוספים
│   ├── pieces/               # תמונות הכלים
│   ├── websocket_server.py   # שרת WebSocket
│   ├── requirements.txt      # תלויות השרת
│   └── main.py              # נקודת כניסה
├── client/
│   ├── ui/                   # רכיבי ממשק משתמש
│   │   ├── pieces/           # תמונות הכלים
│   │   ├── Board.py          # לוח לקליינט
│   │   ├── Graphics.py       # גרפיקה לקליינט
│   │   └── ...              # קבצים נוספים
│   ├── websocket_client.py   # קליינט WebSocket
│   ├── game_client.py        # קליינט גרפי
│   ├── simple_client.py      # קליינט פשוט לבדיקות
│   ├── white_player.py       # אפליקציה לשחקן הלבן
│   ├── black_player.py       # אפליקציה לשחקן השחור
│   └── requirements.txt      # תלויות הקליינט
└── README.md                # התיעוד הזה
```

## 🚀 התקנה והפעלה

### דרישות מערכת
- Python 3.8+
- Linux/Ubuntu (נבדק על Ubuntu)
- חיבור לאינטרנט להתקנת חבילות

### התקנה מהירה

1. **התקנת תלויות השרת:**
```bash
cd server
pip install -r requirements.txt
```

2. **התקנת תלויות הקליינט:**
```bash
cd ../client
pip install -r requirements.txt
# להתקנת tkinter במערכת Ubuntu:
sudo apt-get install python3-tk
```

### הפעלה מדריך

1. **הפעלת השרת (טרמינל ראשון):**
```bash
cd server
python3 websocket_server.py
```

2. **הפעלת הקליינט הלבן (טרמינל שני):**
```bash
cd client
python3 white_player.py
```

3. **הפעלת הקליינט השחור (טרמינל שלישי):**
```bash
cd client
python3 black_player.py
```

### בדיקה ללא GUI

לבדיקת החיבור ללא ממשק גרפי:
```bash
cd client
python3 simple_client.py
```

## 🎮 כיצד לשחק

1. **חיבור**: הפעל את השרת ולאחר מכן את שני הקליינטים
2. **זיהוי צבעים**: הקליינט הראשון יהיה לבן, השני שחור
3. **הזזת כלים**: לחץ על כלי ולאחר מכן על היעד הרצוי
4. **משחק מקביל**: שני השחקנים יכולים להזיז בו-זמנית!
5. **ניצחון**: המטרה היא לתפוס את מלך היריב

## 🔧 פרוטוקול תקשורת

### Client → Server
```json
{
  "type": "move",
  "piece_id": "PW_0",
  "move_type": "move", 
  "params": ["e2", "e4"]
}
```

### Server → Client
```json
{
  "type": "game_state",
  "pieces": [
    {
      "id": "PW_0",
      "position": [6, 4],
      "state": "IdleState"
    }
  ],
  "game_time": 1234,
  "board_size": [8, 8],
  "is_game_over": false
}
```

### הודעות נוספות
- `welcome`: קבלת פנים לקליינט חדש
- `error`: שגיאות (מהלכים לא חוקיים)
- `game_over`: סיום משחק

## 🧪 בדיקות

להפעלת בדיקות (אם קיימות):
```bash
cd server
python -m pytest tests/ -v

cd ../client  
python -m pytest tests/ -v
```

## 🎨 תכונות מתקדמות

- ✅ **משחק בזמן אמת**: תקשורת WebSocket מהירה
- ✅ **גרפיקה מלאה**: שימוש בתמונות מהמשחק המקורי
- ✅ **ארכיטקטורה מודולרית**: הפרדה בין לוגיקה לממשק
- ✅ **תמיכה במקביליות**: שני שחקנים בו-זמנית
- ✅ **וולידציה מלאה**: בדיקת חוקיות מהלכים
- ✅ **מצב קליינט/שרת**: אפשרות למשחק רשת

## 🐛 פתרון בעיות

### השרת לא מתחיל
```bash
# בדוק שהפורט זמין
netstat -tulpn | grep 8765
# אם תפוס, שנה פורט או הרוג תהליך
```

### הקליינט לא מתחבר
```bash
# וודא שהשרת פועל
curl http://localhost:8765/health  # אם יש endpoint
# בדוק חומת אש
sudo ufw status
```

### בעיות גרפיקה
```bash
# התקן tkinter
sudo apt-get install python3-tk
# בדוק תמיכה בגרפיקה
python3 -c "import tkinter; print('GUI OK')"
```

### בעיות בספריות
```bash
# התקן OpenCV אם חסר
pip install opencv-python
# התקן numpy
pip install numpy
```

## 🔮 העתיד

רעיונות להרחבות:
- 🌐 תמיכה ביותר משני שחקנים
- 📱 קליינט נייד
- 🎵 אפקטי קול
- 🏆 מערכת ניקוד
- 📊 סטטיסטיקות משחק
- 🎨 עיצובים נוספים
- 🤖 שחקן מחשב (AI)

## 👥 תרומה

לתרומה לפרויקט:
1. צור Fork
2. צור branch חדש
3. בצע שינויים
4. שלח Pull Request

## 📜 רישיון

פרויקט זה מבוסס על הקוד המקורי מ-CTD25_Solutions ומותאם לארכיטקטורת Client/Server.

---

**🎮 תהנו מהמשחק! 🎮**

> "במשחק Kung Fu Chess, המהירות חשובה לא פחות מהאסטרטגיה"