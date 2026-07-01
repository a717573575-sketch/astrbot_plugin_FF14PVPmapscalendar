import asyncio
import os
import tempfile
from playwright.async_api import async_playwright
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp

# ==================== 内嵌的 HTML 页面（浅色背景+高对比文字） ====================
HTML_CONTENT = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PVP赛季日历</title>
    <style>
        *, ::before, ::after { box-sizing: border-box; border-width: 0; border-style: solid; }
        html { line-height: 1.5; -webkit-text-size-adjust: 100%; font-family: system-ui, -apple-system, sans-serif; }
        body { 
            margin: 0; 
            padding: 0; 
            height: 100%; 
            background: #f0f2f5;
            color: #1e293b;
            font-family: system-ui, -apple-system, sans-serif; 
        }
        .container { width: 100%; max-width: 1200px; margin: 0 auto; padding: 1rem 1.5rem; }
        .text-center { text-align: center; }
        .text-primary { color: #f59e0b; }
        .text-white { color: #1e293b; }
        .text-gray-300 { color: #475569; }
        .font-bold { font-weight: 700; }
        .text-3xl { font-size: 1.875rem; line-height: 2.25rem; }
        .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
        .text-xs { font-size: 0.75rem; line-height: 1rem; }
        .text-xl { font-size: 1.25rem; line-height: 1.75rem; }
        .text-2xl { font-size: 1.5rem; line-height: 2rem; }
        .mb-1 { margin-bottom: 0.25rem; }
        .mb-2 { margin-bottom: 0.5rem; }
        .mb-4 { margin-bottom: 1rem; }
        .mb-6 { margin-bottom: 1.5rem; }
        .flex { display: flex; }
        .flex-col { flex-direction: column; }
        .flex-1 { flex: 1 1 0%; }
        .items-center { align-items: center; }
        .justify-center { justify-content: center; }
        .justify-between { justify-content: space-between; }
        .gap-2 { gap: 0.5rem; }
        .gap-3 { gap: 0.75rem; }
        .gap-4 { gap: 1rem; }
        .gap-6 { gap: 1.5rem; }
        .rounded-lg { border-radius: 0.5rem; }
        .rounded-xl { border-radius: 0.75rem; }
        .p-3 { padding: 0.75rem; }
        .p-4 { padding: 1rem; }
        .shadow-lg { box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
        .grid { display: grid; }
        .grid-cols-7 { grid-template-columns: repeat(7, 1fr); }
        .min-w-0 { min-width: 0; }
        .w-full { width: 100%; }
        .h-auto { height: auto; }
        .font-mono { font-family: monospace; }
        .opacity-80 { opacity: 0.8; }
        .opacity-70 { opacity: 0.7; }
        .lg\:flex-row { flex-direction: column; }
        .lg\:h-full { height: 100%; }
        .lg\:w-\[360px\] { width: 100%; }
        @media (min-width: 1024px) {
            .lg\:flex-row { flex-direction: row; }
            .lg\:w-\[360px\] { width: 360px; }
        }
        .text-shadow-lg { text-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .text-shadow-sm { text-shadow: none; }
        .calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 0.75rem; flex: 1; }
        .calendar-day {
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            background: rgba(255,255,255,0.8);
            border: 1px solid rgba(0,0,0,0.08);
            border-radius: 0.5rem;
            min-height: 50px; position: relative;
            transition: all 0.2s ease;
        }
        .calendar-day.today {
            border: 3px solid #f59e0b;
            box-shadow: 0 0 0 3px rgba(245,158,11,0.3), 0 0 15px rgba(245,158,11,0.3);
            background: rgba(245,158,11,0.1);
        }
        .map-badge {
            width: 36px; height: 36px; border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            margin-bottom: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 2px solid rgba(255,255,255,0.3); color: white;
        }
        .map-badge-text {
            font-size: 18px;
            font-weight: 800;
            line-height: 1;
        }
        .day-number { font-size: 12px; font-weight: 600; color: #334155; }
        .tooltip { display: none; }
        .map-legend { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(0,0,0,0.1); }
        .legend-item { display: flex; align-items: center; gap: 0.5rem; font-size: 12px; color: #1e293b; }
        .legend-badge {
            width: 24px; height: 24px; border-radius: 6px;
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); color: white;
        }
        .legend-badge-text {
            font-size: 14px;
            font-weight: 700;
            line-height: 1;
        }
        .glass-effect {
            background: rgba(255,255,255,0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.5);
            box-shadow: 0 8px 20px rgba(0,0,0,0.08);
            border-radius: 1rem;
        }
        .weekday-header {
            background: rgba(255,255,255,0.7);
            border-radius: 0.5rem;
            padding: 0.5rem;
            font-weight: 600;
            color: #475569;
            font-size: 11px;
            text-align: center;
        }
        .weekday-header:nth-child(6), .weekday-header:nth-child(7) { color: #f59e0b; }
        .month-nav-btn {
            background: rgba(255,255,255,0.8);
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 0.5rem;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #475569;
            cursor: pointer;
            transition: 0.1s;
        }
        .month-nav-btn:hover {
            background: #f59e0b;
            color: white;
        }
        h1, h2, h3 {
            color: #0f172a;
        }
        .text-gray-200 {
            color: #334155;
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="text-center mb-6">
            <h1 class="text-3xl font-bold text-primary text-shadow-lg mb-2">PVP赛季日历</h1>
            <p class="text-gray-300 text-sm">查看当前赛季的地图安排</p>
        </header>

        <div class="flex flex-col lg:flex-row gap-6 h-auto lg:h-[720px]">
            <div class="flex-1 min-w-0 flex flex-col h-auto lg:h-full">
                <div class="glass-effect rounded-xl p-4 shadow-lg flex flex-col h-full">
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="text-xl font-bold text-primary" id="calendar-title">2026年5月</h2>
                        <div class="flex gap-2">
                            <button id="prev-month" class="month-nav-btn">◀</button>
                            <button id="next-month" class="month-nav-btn">▶</button>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-7 gap-2 mb-2">
                        <div class="weekday-header">一</div><div class="weekday-header">二</div><div class="weekday-header">三</div>
                        <div class="weekday-header">四</div><div class="weekday-header">五</div><div class="weekday-header">六</div><div class="weekday-header">日</div>
                    </div>
                    
                    <div id="calendar-grid" class="calendar-grid"></div>
                    
                    <div class="map-legend">
                        <div class="legend-item"><div class="legend-badge" style="background:#f59e0b"><span class="legend-badge-text">尘</span></div><span>尘封秘岩</span></div>
                        <div class="legend-item"><div class="legend-badge" style="background:#3b82f6"><span class="legend-badge-text">荣</span></div><span>荣誉野</span></div>
                        <div class="legend-item"><div class="legend-badge" style="background:#10b981"><span class="legend-badge-text">昂</span></div><span>昂萨哈凯尔</span></div>
                        <div class="legend-item"><div class="legend-badge" style="background:#ef4444"><span class="legend-badge-text">沃</span></div><span>沃刻其特</span></div>
                        <div class="legend-item"><div class="legend-badge" style="background:#8b5cf6"><span class="legend-badge-text">周</span></div><span>周边遗迹群</span></div>
                    </div>
                </div>
            </div>

            <div class="w-full lg:w-[360px] flex flex-col gap-4 h-auto lg:h-full">
                <div class="glass-effect rounded-xl p-3 text-center">
                    <div class="text-xl font-mono font-bold text-primary" id="current-date-display"></div>
                    <div class="text-2xl font-mono font-bold text-gray-800" id="current-time-display"></div>
                </div>

                <div class="glass-effect rounded-xl p-3 flex-1">
                    <h3 class="text-sm font-semibold text-gray-600 mb-2">当前地图</h3>
                    <div class="flex items-center gap-3 mb-2">
                        <div class="map-badge" style="width:48px;height:48px;border-radius:12px;" id="current-map-badge">
                            <span class="map-badge-text" style="font-size:24px;"></span>
                        </div>
                        <div><h4 class="text-base font-bold" id="current-map-name"></h4></div>
                    </div>
                    <p class="text-xs text-gray-600" id="current-map-desc"></p>
                </div>

                <div class="glass-effect rounded-xl p-3 text-center">
                    <div class="text-xs font-semibold text-gray-600 mb-1">距离轮换</div>
                    <div class="text-2xl font-mono font-bold text-primary" id="countdown-display"></div>
                </div>

                <div class="glass-effect rounded-xl p-3 flex-1">
                    <h3 class="text-sm font-semibold text-gray-600 mb-2">下个地图</h3>
                    <div class="flex items-center gap-3 mb-2">
                        <div class="map-badge" style="width:48px;height:48px;border-radius:12px;" id="next-map-badge">
                            <span class="map-badge-text" style="font-size:24px;"></span>
                        </div>
                        <div><h4 class="text-base font-bold" id="next-map-name"></h4></div>
                    </div>
                    <p class="text-xs text-gray-600" id="next-map-desc"></p>
                </div>
            </div>
        </div>
    </div>

    <script>
        const MAP_INFO = {
            chen: {
                name: '尘封秘岩',
                color: '#f59e0b',
                firstChar: '尘',
                desc: '利姆萨·罗敏萨的船员们都在说，艾欧泽亚的海上有座会动的岛……有一天，人们终于找到了这座被称为"彷徨的燕尾岩"的传说中的岛——尘封秘岩。但是，这座岛屿勾起的不仅仅是人们的冒险心。没过多久就接到了调查队的报告，说这座岛是古代亚拉戈文明所建造的人工岛，曾多次进行过包含欧米茄在内的对蛮神技术实验。人们为了获得古代亚拉戈遗物中的"情报"，便在这里展开了争夺"情报"的斗争。'
            },
            rongyu: {
                name: '荣誉野',
                color: '#3b82f6',
                firstChar: '荣',
                desc: '库尔札斯东部低地的荣誉野，因加雷马帝国第七军团团长奈尔·范·达纳斯在此发现了用以诱导"卫月"的古代遗迹浮岛而为世人所知。在这片土地上，又有新的古代亚拉戈文明的遗物被发现了。就这样，艾欧泽亚城邦军事同盟将这片冻结的山岳地带指定为了新的"法外战区"。循着奈尔遗留下的线索，粉碎冻结的遗物，火热的战斗即将展开！'
            },
            angsaha: {
                name: '昂萨哈凯尔',
                color: '#10b981',
                firstChar: '昂',
                desc: '太阳神草原中央的昂萨哈凯尔有着丰富的水源，暮晖之民的各个部落为了获得这片肥沃土地的支配权展开了激烈的竞争。其中奥勒奔部与黑涡团结盟、艾金部与双蛇党结盟、而呼洛部则与恒辉队结盟，纷纷增强了自己的战力。冒险者们啊，为了各自同盟部落的名誉，奋勇参加争夺土地支配权的"那达慕"，与"无垢的大地"订下契约吧！'
            },
            woke: {
                name: '沃刻其特',
                color: '#ef4444',
                firstChar: '沃',
                desc: '从艾欧泽亚向西出发，越过苍茫洋便能抵达图拉尔大陆。那片大陆的某个山区有一座名为"沃刻其特"的大山。"沃刻其特"的意思是"雪之霸主"，相传这附近在很久以前曾爆发过一场激烈的尤卡巨人族内战。机缘巧合之下，正在寻找联合训练场地的黑涡团、双蛇党以及恒辉队正式借用了这片古老的战场，启动了以局部战争为背景的演习。于是，在这座雪精静静守望的山脉之中，冒险者部队之间的模拟战即将打响。'
            },
            yiji: {
                name: '周边遗迹群',
                color: '#8b5cf6',
                firstChar: '周',
                desc: '加尔提诺平原，第七灵灾的根源之地，因为灵灾带来的巨大变化，导致地下埋藏的古代亚拉戈文明的遗迹显露了出来。为了争夺这片遗迹的所有权，即使是已经缔结了联盟的三国也变得针锋相对了起来，甚至做出了一切纷争只发生在这片地区，绝不带到外面来的协定。于是，这片加尔提诺平原变成了法理之外的前线战场，三国为了占领周边遗迹群而派出了各国军队中的冒险者连队。'
            }
        };

        const CYCLE = ['chen','rongyu','angsaha','woke','chen','yiji','angsaha','woke'];

        function getMapIndexForDate(date) {
            const baseDate = new Date(2026, 4, 17);
            const diffDays = Math.floor((date - baseDate) / (1000 * 60 * 60 * 24));
            return ((7 + diffDays) % 8 + 8) % 8;
        }

        function updateInfoPanel() {
            const now = new Date();
            document.getElementById('current-date-display').textContent = (now.getMonth()+1) + '月' + now.getDate() + '日';
            document.getElementById('current-time-display').textContent = 
                String(now.getHours()).padStart(2,'0') + ':' + String(now.getMinutes()).padStart(2,'0') + ':' + String(now.getSeconds()).padStart(2,'0');

            const idx = getMapIndexForDate(new Date(now.getTime() + 60*60*1000));
            const nextIdx = (idx + 1) % 8;
            const info = MAP_INFO[CYCLE[idx]];
            const nextInfo = MAP_INFO[CYCLE[nextIdx]];

            const curBadge = document.getElementById('current-map-badge');
            curBadge.style.backgroundColor = info.color;
            curBadge.innerHTML = '<span class="map-badge-text" style="font-size:24px;">' + info.firstChar + '</span>';
            document.getElementById('current-map-name').textContent = info.name;
            document.getElementById('current-map-name').style.color = info.color;
            document.getElementById('current-map-desc').textContent = info.desc;

            const nextBadge = document.getElementById('next-map-badge');
            nextBadge.style.backgroundColor = nextInfo.color;
            nextBadge.innerHTML = '<span class="map-badge-text" style="font-size:24px;">' + nextInfo.firstChar + '</span>';
            document.getElementById('next-map-name').textContent = nextInfo.name;
            document.getElementById('next-map-name').style.color = nextInfo.color;
            document.getElementById('next-map-desc').textContent = nextInfo.desc;

            const nextRotation = new Date(now);
            if (now.getHours() >= 23) nextRotation.setDate(now.getDate()+1);
            nextRotation.setHours(23,0,0,0);
            const diff = nextRotation - now;
            const h = Math.floor(diff / 3600000);
            const m = Math.floor((diff % 3600000) / 60000);
            const s = Math.floor((diff % 60000) / 1000);
            document.getElementById('countdown-display').textContent = 
                String(h).padStart(2,'0') + ':' + String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
        }

        function renderCalendar(year, month) {
            document.getElementById('calendar-title').textContent = year + '年' + (month+1) + '月';
            const grid = document.getElementById('calendar-grid');
            grid.innerHTML = '';
            const firstDay = new Date(year, month, 1).getDay() || 7;
            const daysInMonth = new Date(year, month+1, 0).getDate();
            const today = new Date();

            for (let i = 1; i < firstDay; i++) {
                const empty = document.createElement('div');
                empty.className = 'calendar-day';
                empty.style.visibility = 'hidden';
                grid.appendChild(empty);
            }

            for (let d = 1; d <= daysInMonth; d++) {
                const date = new Date(year, month, d);
                const idx = getMapIndexForDate(date);
                const info = MAP_INFO[CYCLE[idx]];
                const isToday = (d === today.getDate() && month === today.getMonth() && year === today.getFullYear());

                const dayEl = document.createElement('div');
                dayEl.className = 'calendar-day rounded-lg' + (isToday ? ' today' : '');
                dayEl.innerHTML = `
                    <div class="map-badge" style="background-color:${info.color}">
                        <span class="map-badge-text">${info.firstChar}</span>
                    </div>
                    <span class="day-number">${d}</span>
                `;
                grid.appendChild(dayEl);
            }

            const total = firstDay - 1 + daysInMonth;
            for (let i = total; i < 42; i++) {
                const empty = document.createElement('div');
                empty.className = 'calendar-day';
                empty.style.visibility = 'hidden';
                grid.appendChild(empty);
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            const now = new Date();
            renderCalendar(now.getFullYear(), now.getMonth());
            updateInfoPanel();
            setInterval(updateInfoPanel, 1000);

            document.getElementById('prev-month').addEventListener('click', () => {
                const parts = document.getElementById('calendar-title').textContent.split(/[年月]/);
                const newDate = new Date(parseInt(parts[0]), parseInt(parts[1]) - 2);
                renderCalendar(newDate.getFullYear(), newDate.getMonth());
            });
            document.getElementById('next-month').addEventListener('click', () => {
                const parts = document.getElementById('calendar-title').textContent.split(/[年月]/);
                const newDate = new Date(parseInt(parts[0]), parseInt(parts[1]));
                renderCalendar(newDate.getFullYear(), newDate.getMonth());
            });
        });
    </script>
</body>
</html>
"""

# ==================== AstrBot 插件类 ====================
@register(
    name="ff14_pvp_map",
    version="1.0.2",       # 更新版本号
    author="情劣等生@红茶川",
    desc="接入astrbot后 输入 /pvp日历 获取FF14 PVP地图网页截图（浅色背景高对比度版，修复超时）",
)
class FF14PvpMap(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.temp_dir = tempfile.gettempdir()

    async def capture_webpage(self) -> str:
        """使用 Playwright 渲染内嵌 HTML 并截图（JPEG）"""
        img_path = os.path.join(self.temp_dir, "ff14_pvp_temp.jpg")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            page = await browser.new_page(viewport={"width": 1365, "height": 911})
            
            await page.set_content(HTML_CONTENT, timeout=30000)
            
            # ✅ 修复：等待 .day-number（只在实际日期格出现，且始终可见）
            await page.wait_for_selector("#calendar-grid .day-number", timeout=15000)
            await page.wait_for_timeout(2000)
            
            await page.screenshot(
                path=img_path,
                type='jpeg',
                quality=90,
                full_page=False
            )
            await browser.close()
        return img_path

    @filter.command("pvp日历")
    async def send_pvp_map(self, event: AstrMessageEvent):
        yield event.plain_result("纷争前线日历查询中，请稍后喵")
        try:
            img_file = await self.capture_webpage()
            msg_chain = [
                Comp.Plain("今天的纷争前线日历来啦！"),
                Comp.Image.fromFileSystem(img_file)
            ]
            yield event.chain_result(msg_chain)

            if os.path.exists(img_file):
                os.remove(img_file)
        except Exception as e:
            yield event.plain_result(f"截图失败！错误：{str(e)}")
