# -*- coding: utf-8 -*-
import json
import os
import time

import arabic_reshaper
try:
    from bidi.algorithm import get_display
except ImportError:
    from bidi import get_display

from kivy.app import App
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

HERE = os.path.dirname(os.path.abspath(__file__))
LabelBase.register(DEFAULT_FONT,
                   os.path.join(HERE, 'fonts', 'font.ttf'),
                   fn_bold=os.path.join(HERE, 'fonts', 'font-bold.ttf'))

GREEN = (0.15, 0.56, 0.28, 1)
DARK = (0.09, 0.38, 0.18, 1)
GRAYBG = (0.94, 0.95, 0.94, 1)
GRAY = (0.55, 0.58, 0.56, 1)
WHITE = (1, 1, 1, 1)
TEXT = (0.13, 0.15, 0.14, 1)
RED = (0.75, 0.15, 0.15, 1)
Window.clearcolor = GRAYBG
Window.softinput_mode = 'below_target'

_reshaper = arabic_reshaper.ArabicReshaper()


def ar(t):
    t = str(t)
    return get_display(_reshaper.reshape(t)) if t else t


def wrap_ar(text, n=24):
    lines, cur = [], ''
    for w in str(text).split(' '):
        if cur and len(cur) + 1 + len(w) > n:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    lines.append(cur)
    return '\n'.join(ar(x) for x in lines)


def msg_label(text, h=80):
    lb = Label(text=wrap_ar(text), color=TEXT, font_size=sp(18),
               halign='center', valign='middle', size_hint_y=None,
               height=dp(h))
    lb.bind(size=lambda *a: setattr(lb, 'text_size', lb.size))
    return lb


def fmt(x):
    x = round(float(x), 2)
    return ('%.2f' % x).rstrip('0').rstrip('.') if x != int(x) else str(int(x))


_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩٫۰۱۲۳۴۵۶۷۸۹', '0123456789.0123456789')

DEFAULT_TYPES = [
    {'name': 'برنيك كبير', 'weight': 2.0},
    {'name': 'برنيك وسط', 'weight': 1.5},
    {'name': 'برنيك صغير', 'weight': 1.0},
]


class Store:
    def __init__(self, path):
        self.path = path
        self.data = {'types': [dict(t) for t in DEFAULT_TYPES],
                     'records': [], 'tally': {}}
        try:
            with open(path, encoding='utf-8') as f:
                self.data.update(json.load(f))
        except Exception:
            pass

    def save(self):
        try:
            tmp = self.path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False)
            os.replace(tmp, self.path)
        except Exception as e:
            print('save error', e)

    @property
    def types(self):
        return self.data['types']


def store():
    return App.get_running_app().store


class Card(BoxLayout):
    def __init__(self, bg=WHITE, radius=12, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            self._c = Color(*bg)
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                       radius=[dp(radius)])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self._r.pos, self._r.size = self.pos, self.size


class L(Label):
    def __init__(self, text='', **kw):
        kw.setdefault('color', TEXT)
        kw.setdefault('font_size', sp(18))
        kw.setdefault('halign', 'right')
        kw.setdefault('valign', 'middle')
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(36))
        kw.setdefault('shorten', True)
        kw.setdefault('shorten_from', 'left')
        super().__init__(text=ar(text), **kw)
        self.bind(size=lambda *a: setattr(self, 'text_size', self.size))

    def set(self, t):
        self.text = ar(t)


class B(Button):
    def __init__(self, text, bg=GREEN, h=60, **kw):
        if 'size_hint' not in kw:
            kw['size_hint_y'] = None
        kw.setdefault('height', dp(h))
        kw.setdefault('font_size', sp(20))
        kw.setdefault('bold', True)
        super().__init__(text=ar(text), background_normal='',
                         background_down='', background_color=bg,
                         color=WHITE, **kw)
        self._bg = bg
        self.bind(state=lambda i, s: setattr(
            i, 'background_color', DARK if s == 'down' and bg == GREEN
            else ((0.4, 0.42, 0.4, 1) if s == 'down' else self._bg)))


def _style(w):
    w.background_normal = ''
    w.background_active = ''
    w.background_color = (1, 1, 1, 1)
    w.foreground_color = TEXT
    w.cursor_color = GREEN
    w.font_size = sp(20)
    w.size_hint_y = None
    w.height = dp(52)
    w.padding = [dp(8), dp(13), dp(8), dp(8)]
    w.multiline = False
    w.write_tab = False


class Num(TextInput):
    def __init__(self, kind='float', **kw):
        if 'hint_text' in kw:
            kw['hint_text'] = ar(kw['hint_text'])
        super().__init__(input_filter=kind, input_type='number',
                         halign='center', **kw)
        _style(self)
        self.hint_text_color = (0.6, 0.6, 0.6, 1)

    def insert_text(self, s, from_undo=False):
        return super().insert_text(s.translate(_DIGITS), from_undo=from_undo)

    def val(self):
        try:
            return float(self.text)
        except ValueError:
            return 0.0


class ArInput(TextInput):
    raw = ''

    def __init__(self, **kw):
        if 'hint_text' in kw:
            kw['hint_text'] = ar(kw['hint_text'])
        super().__init__(halign='right', keyboard_suggestions=False, **kw)
        _style(self)
        self.hint_text_color = (0.6, 0.6, 0.6, 1)

    def _show(self):
        self.text = ar(self.raw)
        self.cursor = self.get_cursor_from_index(len(self.text))

    def set_raw(self, s):
        self.raw = s
        self._show()

    def insert_text(self, s, from_undo=False):
        self.raw += s.replace('\n', ' ')
        self._show()

    def do_backspace(self, from_undo=False, mode='bkspc'):
        self.raw = self.raw[:-1]
        self._show()

    def delete_selection(self, from_undo=False):
        self.raw = ''
        self._show()


def make_spinner(text, values):
    return Spinner(text=text, values=values, font_size=sp(17),
                   background_normal='', background_down='',
                   background_color=GREEN, color=WHITE)


def lines_view(lines, h=34):
    sv = ScrollView()
    box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
    box.bind(minimum_height=box.setter('height'))
    for t in lines:
        box.add_widget(L(t, height=dp(h), font_size=sp(17)))
    sv.add_widget(box)
    return sv


def popup(title, content, h=300):
    p = Popup(title=ar(title), content=content, size_hint=(.92, None),
              height=dp(h), title_size=sp(19), title_align='center',
              separator_color=GREEN, auto_dismiss=False)
    p.open()
    return p


def message(title, text):
    box = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(10))
    box.add_widget(msg_label(text))
    b = B('حسنًا')
    box.add_widget(b)
    p = popup(title, box, 230)
    b.bind(on_release=p.dismiss)


def confirm(title, text, on_yes):
    box = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(10))
    box.add_widget(msg_label(text))
    row = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
    yes = B('نعم', bg=RED)
    no = B('إلغاء', bg=GRAY)
    row.add_widget(no)
    row.add_widget(yes)
    box.add_widget(row)
    p = popup(title, box, 240)
    no.bind(on_release=p.dismiss)

    def _y(*a):
        p.dismiss()
        on_yes()
    yes.bind(on_release=_y)


class Page(Screen):
    title = ''
    back = True

    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical')
        bar = Card(bg=GREEN, radius=0, size_hint_y=None, height=dp(62),
                   padding=dp(8), spacing=dp(8))
        bar.add_widget(L(self.title, color=WHITE, font_size=sp(22),
                         bold=True, halign='center', height=dp(62)))
        if self.back:
            bk = B('رجوع', bg=DARK, h=46, size_hint=(None, None),
                   width=dp(90), height=dp(46), pos_hint={'center_y': .5})
            bk.bind(on_release=lambda *a: App.get_running_app().go('home'))
            bar.add_widget(bk)
        sv = ScrollView(bar_width=dp(4))
        self.body = BoxLayout(orientation='vertical', size_hint_y=None,
                              padding=dp(12), spacing=dp(10))
        self.body.bind(minimum_height=self.body.setter('height'))
        sv.add_widget(self.body)
        root.add_widget(bar)
        root.add_widget(sv)
        self.add_widget(root)
        self.build()

    def build(self):
        pass


class HomePage(Page):
    title = 'تصفية العربيات'
    back = False

    def build(self):
        self.body.padding = [dp(16), dp(24)]
        self.body.spacing = dp(18)
        self.body.add_widget(L('اختر ما تريد:', font_size=sp(20), bold=True))
        for txt, scr in (('تصفية عربية', 'clear'),
                         ('جمع البرانيك', 'collect'),
                         ('سجل العمليات', 'history'),
                         ('إعداد أنواع البرانيك', 'settings')):
            b = B(txt, h=95, font_size=sp(26))
            b.bind(on_release=lambda i, s=scr: App.get_running_app().go(s))
            self.body.add_widget(b)


class CrateRow(BoxLayout):
    def __init__(self, page, **kw):
        super().__init__(size_hint_y=None, height=dp(56), spacing=dp(6), **kw)
        self.page = page
        self.map = {ar(t['name']): t for t in store().types}
        names = list(self.map)
        self.spin = make_spinner(names[0] if names else ar('اختر'), names)
        self.spin.size_hint_x = .42
        self.empty = Num(hint_text='فارغ', size_hint_x=.30)
        self.count = Num(kind='int', hint_text='العدد', size_hint_x=.28)
        self.spin.height = dp(52)
        self.spin.size_hint_y = None
        self.on_type()
        self.spin.bind(text=self.on_type)
        self.empty.bind(text=page.calc)
        self.count.bind(text=page.calc)
        for w in (self.count, self.empty, self.spin):
            self.add_widget(w)

    def on_type(self, *a):
        t = self.map.get(self.spin.text)
        self.empty.text = fmt(t['weight']) if t else ''

    def data(self):
        t = self.map.get(self.spin.text)
        return {'name': t['name'] if t else '',
                'empty': self.empty.val(), 'count': int(self.count.val())}


class ClearPage(Page):
    title = 'تصفية عربية'

    def build(self):
        b = self.body
        b.add_widget(L('اسم العربية أو صاحبها (اختياري)'))
        self.name = ArInput(hint_text='مثال: عربية أحمد')
        b.add_widget(self.name)
        b.add_widget(L('الوزن الإجمالي للعربية (كجم)'))
        self.gross = Num(hint_text='0')
        self.gross.bind(text=self.calc)
        b.add_widget(self.gross)

        b.add_widget(L('البرانيك (حتى 4 أنواع)', bold=True))
        head = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6))
        for t, x in (('العدد', .28), ('وزن فارغ', .30), ('النوع', .42)):
            head.add_widget(L(t, halign='center', size_hint_x=x,
                              height=dp(28), font_size=sp(15), color=GRAY))
        b.add_widget(head)
        self.rows_box = BoxLayout(orientation='vertical', size_hint_y=None,
                                  spacing=dp(6))
        self.rows_box.bind(minimum_height=self.rows_box.setter('height'))
        b.add_widget(self.rows_box)
        self.rows = []

        ctl = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(8))
        self.del_btn = B('حذف نوع', bg=GRAY, h=54)
        self.add_btn = B('+ إضافة نوع', h=54)
        self.del_btn.bind(on_release=self.del_row)
        self.add_btn.bind(on_release=self.add_row)
        ctl.add_widget(self.del_btn)
        ctl.add_widget(self.add_btn)
        b.add_widget(ctl)

        card = Card(orientation='vertical', size_hint_y=None, height=dp(190),
                    padding=dp(12), spacing=dp(4))
        self.l_cnt = L('')
        self.l_w = L('')
        self.l_net = L('', font_size=sp(23), bold=True, height=dp(56))
        for w in (self.l_cnt, self.l_w, self.l_net):
            card.add_widget(w)
        b.add_widget(card)

        save = B('حفظ العملية', h=70, font_size=sp(24))
        save.bind(on_release=self.save)
        rst = B('تفريغ الشاشة', bg=GRAY, h=54)
        rst.bind(on_release=lambda *a: self.reset())
        b.add_widget(save)
        b.add_widget(rst)
        self.reset()

    def on_pre_enter(self, *a):
        old = [r.data() for r in self.rows]
        self.rows_box.clear_widgets()
        self.rows = []
        for d in old or [None]:
            self.add_row(None, d)

    def add_row(self, inst=None, d=None):
        if len(self.rows) >= 4:
            return
        r = CrateRow(self)
        if d:
            for k, t in r.map.items():
                if t['name'] == d['name']:
                    r.spin.text = k
            r.empty.text = fmt(d['empty'])
            r.count.text = str(d['count']) if d['count'] else ''
        self.rows.append(r)
        self.rows_box.add_widget(r)
        self.refresh_btns()
        self.calc()

    def del_row(self, *a):
        if len(self.rows) > 1:
            self.rows_box.remove_widget(self.rows.pop())
            self.refresh_btns()
            self.calc()

    def refresh_btns(self):
        self.add_btn.disabled = len(self.rows) >= 4
        self.del_btn.disabled = len(self.rows) <= 1

    def totals(self):
        cnt = sum(r.data()['count'] for r in self.rows)
        w = sum(r.data()['count'] * r.data()['empty'] for r in self.rows)
        return cnt, w, self.gross.val() - w

    def calc(self, *a):
        if not self.rows:
            return
        cnt, w, net = self.totals()
        self.l_cnt.set('عدد البرانيك: %d' % cnt)
        self.l_w.set('إجمالي وزن البرانيك: %s كجم' % fmt(w))
        self.l_net.set('الوزن الصافي: %s كجم' % fmt(net))
        self.l_net.color = RED if net < 0 else DARK

    def reset(self):
        self.name.set_raw('')
        self.gross.text = ''
        self.rows_box.clear_widgets()
        self.rows = []
        self.add_row()

    def save(self, *a):
        gross = self.gross.val()
        cnt, w, net = self.totals()
        if gross <= 0:
            return message('تنبيه', 'أدخل الوزن الإجمالي للعربية')
        if net < 0:
            return message('تنبيه', 'وزن البرانيك أكبر من الوزن الإجمالي')
        rows = [r.data() for r in self.rows if r.data()['count'] > 0]
        s = store()
        s.data['records'].insert(0, {
            'id': int(time.time() * 1000),
            'date': time.strftime('%Y-%m-%d %H:%M'),
            'name': self.name.raw.strip(), 'gross': gross, 'rows': rows,
            'crates_count': cnt, 'crates_weight': w, 'net': net})
        s.save()
        message('تم', 'تم حفظ العملية. الصافي: %s كجم' % fmt(net))
        self.reset()


class CollectPage(Page):
    title = 'جمع البرانيك'

    def build(self):
        self.items = []
        self.list_box = BoxLayout(orientation='vertical', size_hint_y=None,
                                  spacing=dp(10))
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.body.add_widget(self.list_box)
        self.card = Card(orientation='vertical', size_hint_y=None,
                         height=dp(120), padding=dp(12), spacing=dp(4),
                         bg=(0.85, 0.94, 0.87, 1))
        self.t_cnt = L('', font_size=sp(20), bold=True)
        self.t_w = L('', font_size=sp(20), bold=True)
        self.card.add_widget(self.t_cnt)
        self.card.add_widget(self.t_w)
        self.body.add_widget(self.card)
        b1 = B('إجمالي البرانيك من السجل', h=56)
        b1.bind(on_release=self.from_history)
        b2 = B('تصفير العدادات', bg=GRAY, h=56)
        b2.bind(on_release=lambda *a: confirm(
            'تصفير', 'هل تريد تصفير كل العدادات؟', self.zero))
        self.body.add_widget(b1)
        self.body.add_widget(b2)

    def on_pre_enter(self, *a):
        self.fill()

    def fill(self):
        self.list_box.clear_widgets()
        self.items = []
        tally = store().data.setdefault('tally', {})
        for t in store().types:
            card = Card(orientation='vertical', size_hint_y=None,
                        height=dp(118), padding=dp(10), spacing=dp(6))
            card.add_widget(L('%s  (فارغ: %s كجم)' % (
                t['name'], fmt(t['weight'])), bold=True, height=dp(30)))
            row = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(6))
            wl = L('', halign='center', size_hint_x=.34, height=dp(58),
                   font_size=sp(16))
            plus = B('+', h=58, size_hint=(.18, None), font_size=sp(30))
            num = Num(kind='int', size_hint_x=.30)
            num.height = dp(58)
            num.text = str(tally.get(t['name'], 0) or '')
            minus = B('−', bg=GRAY, h=58, size_hint=(.18, None),
                      font_size=sp(30))
            plus.bind(on_release=lambda i, n=num: self.step(n, 1))
            minus.bind(on_release=lambda i, n=num: self.step(n, -1))
            num.bind(text=self.update)
            for w in (wl, plus, num, minus):
                row.add_widget(w)
            card.add_widget(row)
            self.list_box.add_widget(card)
            self.items.append((t, num, wl))
        if not self.items:
            self.list_box.add_widget(L('أضف أنواع البرانيك من الإعدادات'))
        self.update()

    def step(self, num, d):
        num.text = str(max(0, int(num.val()) + d))

    def update(self, *a):
        tally = store().data.setdefault('tally', {})
        tc, tw = 0, 0.0
        for t, num, wl in self.items:
            c = int(num.val())
            w = c * t['weight']
            wl.set('%s كجم' % fmt(w))
            tally[t['name']] = c
            tc += c
            tw += w
        store().save()
        self.t_cnt.set('إجمالي العدد: %d برنيك' % tc)
        self.t_w.set('إجمالي الوزن: %s كجم' % fmt(tw))

    def zero(self):
        store().data['tally'] = {}
        store().save()
        self.fill()

    def from_history(self, *a):
        agg = {}
        for rec in store().data['records']:
            for r in rec['rows']:
                c, w = agg.get(r['name'], (0, 0.0))
                agg[r['name']] = (c + r['count'], w + r['count'] * r['empty'])
        if not agg:
            return message('السجل', 'لا توجد عمليات محفوظة')
        lines, tc, tw = [], 0, 0.0
        for n, (c, w) in agg.items():
            lines.append('%s: %d برنيك - %s كجم' % (n, c, fmt(w)))
            tc += c
            tw += w
        lines.append('الإجمالي: %d برنيك - %s كجم' % (tc, fmt(tw)))
        box = BoxLayout(orientation='vertical', spacing=dp(8))
        box.add_widget(lines_view(lines))
        b = B('إغلاق', h=54)
        box.add_widget(b)
        p = popup('البرانيك في كل العمليات', box, 420)
        b.bind(on_release=p.dismiss)


class RecordCard(Button):
    def __init__(self, rec, **kw):
        l1 = '%s   %s' % (rec['date'], rec['name'])
        l2 = 'صافي: %s كجم  |  إجمالي: %s كجم' % (
            fmt(rec['net']), fmt(rec['gross']))
        super().__init__(text=ar(l1) + '\n' + ar(l2), halign='right',
                         valign='middle', font_size=sp(16),
                         background_normal='', background_down='',
                         background_color=WHITE, color=TEXT,
                         size_hint_y=None, height=dp(84),
                         padding=(dp(12), dp(6)), **kw)
        self.bind(size=lambda *a: setattr(self, 'text_size', self.size))


class HistoryPage(Page):
    title = 'سجل العمليات'

    def on_pre_enter(self, *a):
        b = self.body
        b.clear_widgets()
        recs = store().data['records']
        if not recs:
            b.add_widget(L('لا توجد عمليات سابقة', halign='center',
                           height=dp(80)))
            return
        tot = sum(r['net'] for r in recs)
        b.add_widget(L('العمليات: %d  |  الصافي: %s كجم' % (
            len(recs), fmt(tot)), bold=True, font_size=sp(16)))
        for rec in recs:
            c = RecordCard(rec)
            c.bind(on_release=lambda i, r=rec: self.show(r))
            b.add_widget(c)
        clr = B('مسح كل السجل', bg=RED, h=54)
        clr.bind(on_release=lambda *a: confirm(
            'مسح السجل', 'سيتم حذف كل العمليات. متأكد؟', self.clear_all))
        b.add_widget(clr)

    def show(self, rec):
        lines = ['التاريخ: ' + rec['date']]
        if rec['name']:
            lines.append('الاسم: ' + rec['name'])
        lines.append('الوزن الإجمالي: %s كجم' % fmt(rec['gross']))
        for r in rec['rows']:
            lines.append('%s: %d × %s = %s كجم' % (
                r['name'], r['count'], fmt(r['empty']),
                fmt(r['count'] * r['empty'])))
        lines.append('إجمالي البرانيك: %d (%s كجم)' % (
            rec['crates_count'], fmt(rec['crates_weight'])))
        lines.append('الوزن الصافي: %s كجم' % fmt(rec['net']))
        box = BoxLayout(orientation='vertical', spacing=dp(8))
        box.add_widget(lines_view(lines))
        row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        close = B('إغلاق', bg=GRAY, h=56)
        dele = B('حذف', bg=RED, h=56)
        row.add_widget(close)
        row.add_widget(dele)
        box.add_widget(row)
        p = popup('تفاصيل العملية', box, 470)
        close.bind(on_release=p.dismiss)

        def _del(*a):
            p.dismiss()
            confirm('حذف', 'حذف هذه العملية؟', lambda: self.delete(rec))
        dele.bind(on_release=_del)

    def delete(self, rec):
        store().data['records'] = [r for r in store().data['records']
                                   if r['id'] != rec['id']]
        store().save()
        self.on_pre_enter()

    def clear_all(self):
        store().data['records'] = []
        store().save()
        self.on_pre_enter()


class SettingsPage(Page):
    title = 'إعداد أنواع البرانيك'

    def build(self):
        b = self.body
        b.add_widget(L('اسم النوع ووزنه وهو فارغ (كجم):', font_size=sp(16)))
        head = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(6))
        head.add_widget(Widget(size_hint_x=None, width=dp(56)))
        head.add_widget(L('الوزن الفارغ', halign='center', size_hint_x=.3,
                          height=dp(26), font_size=sp(15), color=GRAY))
        head.add_widget(L('الاسم', size_hint_x=.7, height=dp(26),
                          font_size=sp(15), color=GRAY))
        b.add_widget(head)
        self.box = BoxLayout(orientation='vertical', size_hint_y=None,
                             spacing=dp(8))
        self.box.bind(minimum_height=self.box.setter('height'))
        b.add_widget(self.box)
        add = B('+ إضافة نوع جديد', h=56)
        add.bind(on_release=lambda *a: self.add_row('', 0))
        sv = B('حفظ الإعدادات', h=70, font_size=sp(24))
        sv.bind(on_release=self.save)
        b.add_widget(add)
        b.add_widget(sv)
        self.rows = []

    def on_pre_enter(self, *a):
        self.box.clear_widgets()
        self.rows = []
        for t in store().types:
            self.add_row(t['name'], t['weight'])

    def add_row(self, name, weight):
        row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(6))
        nm = ArInput(size_hint_x=.7)
        nm.set_raw(name)
        wt = Num(size_hint_x=.3, hint_text='كجم')
        wt.text = fmt(weight) if weight else ''
        dl = B('×', bg=RED, h=52, size_hint=(None, None), width=dp(56),
               font_size=sp(26))
        item = (row, nm, wt)
        dl.bind(on_release=lambda *a: self.remove(item))
        for w in (dl, wt, nm):
            row.add_widget(w)
        self.rows.append(item)
        self.box.add_widget(row)

    def remove(self, item):
        self.box.remove_widget(item[0])
        self.rows.remove(item)

    def save(self, *a):
        types = []
        for _, nm, wt in self.rows:
            n = nm.raw.strip()
            if not n:
                continue
            if wt.val() <= 0:
                return message('تنبيه', 'أدخل وزنًا صحيحًا للنوع: ' + n)
            types.append({'name': n, 'weight': wt.val()})
        if not types:
            return message('تنبيه', 'أضف نوعًا واحدًا على الأقل')
        store().data['types'] = types
        store().save()
        message('تم', 'تم حفظ الإعدادات')


class TasfiyaApp(App):
    title = 'تصفية العربيات'

    def build(self):
        self.store = Store(os.path.join(self.user_data_dir, 'data.json'))
        self.sm = ScreenManager(transition=NoTransition())
        for name, cls in (('home', HomePage), ('clear', ClearPage),
                          ('collect', CollectPage), ('history', HistoryPage),
                          ('settings', SettingsPage)):
            self.sm.add_widget(cls(name=name))
        Window.bind(on_keyboard=self.on_key)
        return self.sm

    def go(self, name):
        self.sm.current = name

    def on_key(self, win, key, *a):
        if key == 27 and self.sm.current != 'home':
            self.go('home')
            return True
        return False

    def on_pause(self):
        self.store.save()
        return True


if __name__ == '__main__':
    TasfiyaApp().run()
