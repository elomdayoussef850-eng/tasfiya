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
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
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

# ألوان التصميم: عاجي + أخضر زمردي + ذهبي
GREEN = (0.02, 0.34, 0.22, 1)
DARK = (0.01, 0.22, 0.15, 1)
GREEN2 = (0.08, 0.48, 0.31, 1)
GOLD = (0.76, 0.57, 0.22, 1)
EDIT = (0.70, 0.45, 0.05, 1)
BG = (0.96, 0.95, 0.91, 1)
WHITE = (1, 1, 1, 1)
TEXT = (0.13, 0.17, 0.15, 1)
GRAY = (0.48, 0.53, 0.50, 1)
RED = (0.72, 0.16, 0.14, 1)
Window.clearcolor = BG
Window.softinput_mode = 'below_target'

PAGE_SIZE = 50
PERIODS = (('all', 'الكل'), ('today', 'اليوم'),
           ('week', '7 أيام'), ('month', 'الشهر'))

_reshaper = arabic_reshaper.ArabicReshaper()

def ar(t):
    t = str(t)
    return get_display(_reshaper.reshape(t)) if t else t

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
        self.data = {'types': [dict(t) for t in DEFAULT_TYPES], 'records': []}
        try:
            with open(path, encoding='utf-8') as f:
                loaded = json.load(f)
            self.data.update(loaded)
            self.data.setdefault('types', [dict(t) for t in DEFAULT_TYPES])
            self.data.setdefault('records', [])
        except Exception:
            pass

    def save(self):
        try:
            tmp = self.path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False)
            os.replace(tmp, self.path)
        except Exception as e:
            print('save error:', e)

    @property
    def types(self):
        return self.data['types']

def store():
    return App.get_running_app().store

class Card(BoxLayout):
    def __init__(self, bg=WHITE, radius=14, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(0, 0, 0, 0.055)
            self.shadow = RoundedRectangle(pos=self.pos, size=self.size,
                                           radius=[dp(radius + 2)])
            self._c = Color(*bg)
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                       radius=[dp(radius)])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self.shadow.pos = (self.x, self.y - dp(2))
        self.shadow.size = self.size
        self._r.pos, self._r.size = self.pos, self.size

class L(Label):
    def __init__(self, text='', **kw):
        kw.setdefault('color', TEXT)
        kw.setdefault('font_size', sp(18))
        kw.setdefault('halign', 'right')
        kw.setdefault('valign', 'middle')
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(38))
        kw.setdefault('shorten', True)
        kw.setdefault('shorten_from', 'left')
        super().__init__(text=ar(text), **kw)
        self.bind(size=lambda *a: setattr(self, 'text_size', self.size))

    def set(self, t):
        self.text = ar(t)

class AccentBar(Widget):
    def __init__(self, color=GREEN, **kw):
        super().__init__(size_hint_x=None, width=dp(5), **kw)
        with self.canvas:
            Color(*color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[dp(3)])
        self.bind(pos=self._u, size=self._u)

    def _u(self, *a):
        self._rect.pos, self._rect.size = self.pos, self.size

class TapCard(ButtonBehavior, Card):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._base = tuple(self._c.rgba)
        self.bind(state=self._press)

    def _press(self, inst, st):
        self._c.rgba = (0.89, 0.93, 0.90, 1) if st == 'down' else self._base

class MenuCard(TapCard):
    def __init__(self, title, sub, **kw):
        super().__init__(orientation='horizontal', size_hint_y=None,
                         height=dp(92), padding=[dp(14), dp(10), dp(8), dp(10)],
                         spacing=dp(10), **kw)
        self.add_widget(L('‹', halign='center', bold=True, color=GOLD,
                          font_size=sp(34), size_hint_x=None, width=dp(30),
                          height=dp(72)))
        mid = BoxLayout(orientation='vertical')
        mid.add_widget(L(title, bold=True, color=GREEN, font_size=sp(21),
                         height=dp(38)))
        mid.add_widget(L(sub, color=GRAY, font_size=sp(14), height=dp(30)))
        self.add_widget(mid)
        self.add_widget(AccentBar(color=GOLD))

class B(Button):
    def __init__(self, text, bg=GREEN, h=56, **kw):
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(h))
        kw.setdefault('font_size', sp(19))
        kw.setdefault('bold', True)
        super().__init__(text=ar(text), background_normal='',
            background_down='', background_color=bg, color=WHITE, **kw)
        self._bg = bg
        self.bind(state=lambda i, s: setattr(
            i, 'background_color', DARK if s == 'down' and bg == GREEN
            else ((0.38, 0.41, 0.39, 1) if s == 'down' else self._bg)))

def style_input(w):
    w.background_normal = ''
    w.background_active = ''
    w.background_color = WHITE
    w.foreground_color = TEXT
    w.cursor_color = GREEN
    w.font_size = sp(18)
    w.size_hint_y = None
    w.height = dp(50)
    w.padding = [dp(9), dp(12), dp(9), dp(8)]
    w.multiline = False
    w.write_tab = False

class Num(TextInput):
    def __init__(self, kind='float', **kw):
        if 'hint_text' in kw:
            kw['hint_text'] = ar(kw['hint_text'])
        super().__init__(input_filter=kind, input_type='number',
                         halign='center', **kw)
        style_input(self)
        self.hint_text_color = (0.55, 0.58, 0.55, 1)

    def insert_text(self, s, from_undo=False):
        return super().insert_text(s.translate(_DIGITS), from_undo=from_undo)

    def val(self):
        try:
            return float(self.text)
        except (ValueError, TypeError):
            return 0.0

class ArInput(TextInput):
    def __init__(self, **kw):
        if 'hint_text' in kw:
            kw['hint_text'] = ar(kw['hint_text'])
        super().__init__(halign='right', keyboard_suggestions=False, **kw)
        style_input(self)
        self.raw = ''
        self.hint_text_color = (0.55, 0.58, 0.55, 1)

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
    return Spinner(text=text, values=values, font_size=sp(16),
        background_normal='', background_down='',
        background_color=GREEN2, color=WHITE)

def lines_view(lines, h=36):
    sv = ScrollView()
    box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
    box.bind(minimum_height=box.setter('height'))
    for t in lines:
        box.add_widget(L(t, height=dp(h), font_size=sp(16)))
    sv.add_widget(box)
    return sv

def popup(title, content, h=300):
    p = Popup(title=ar(title), content=content, size_hint=(.92, None),
        height=dp(h), title_size=sp(18), title_align='center',
        separator_color=GOLD, auto_dismiss=False)
    p.open()
    return p

def message(title, text):
    box = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(10))
    lb = L(text, halign='center', height=dp(90), shorten=False)
    box.add_widget(lb)
    b = B('حسنًا')
    box.add_widget(b)
    p = popup(title, box, 240)
    b.bind(on_release=p.dismiss)

def confirm(title, text, on_yes):
    box = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(10))
    box.add_widget(L(text, halign='center', height=dp(90), shorten=False))
    row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(10))
    yes, no = B('نعم', bg=RED), B('إلغاء', bg=GRAY)
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
        root = BoxLayout(orientation='vertical', spacing=0)

        bar = Card(bg=GREEN, radius=0, size_hint_y=None,
                   height=dp(62), padding=dp(8), spacing=dp(8))
        bar.add_widget(L(self.title, color=WHITE, font_size=sp(22),
                         bold=True, halign='center', height=dp(58)))
        if self.back:
            bk = B('رجوع', bg=DARK, h=44, size_hint=(None, None),
                   width=dp(82), height=dp(44))
            bk.bind(on_release=lambda *a: App.get_running_app().go('home'))
            bar.add_widget(bk)

        sv = ScrollView(bar_width=dp(3))
        self.body = BoxLayout(orientation='vertical', size_hint_y=None,
                              padding=[dp(12), dp(14)], spacing=dp(10))
        self.body.bind(minimum_height=self.body.setter('height'))
        sv.add_widget(self.body)
        root.add_widget(bar)
        root.add_widget(sv)

        # تذييل ثابت أسفل الشاشة
        footer = BoxLayout(size_hint_y=None, height=dp(38), padding=[dp(8), 0])
        with footer.canvas.before:
            Color(*DARK)
            self.footer_bg = RoundedRectangle(pos=footer.pos, size=footer.size,
                                              radius=[dp(0)])
        footer.bind(pos=lambda i, v: setattr(self.footer_bg, 'pos', v),
                    size=lambda i, v: setattr(self.footer_bg, 'size', v))
        footer.add_widget(L('المهندس يوسف شعبان', color=(0.96, 0.80, 0.43, 1),
                            bold=True, halign='center', height=dp(36),
                            font_size=sp(15)))
        root.add_widget(footer)
        self.add_widget(root)
        self.build()

    def build(self):
        pass

class HomePage(Page):
    title = 'تصفية العربيات'
    back = False

    def build(self):
        self.body.padding = [dp(16), dp(22)]
        self.body.spacing = dp(14)
        hero = Card(orientation='vertical', bg=WHITE, size_hint_y=None,
                    height=dp(132), padding=dp(12), spacing=dp(4))
        hero.add_widget(L('نظام إدارة وتصفية أوزان العربيات',
                          halign='center', bold=True, color=GREEN,
                          font_size=sp(21), height=dp(58)))
        hero.add_widget(L('حساب البرانيك والوزن الصافي بسهولة ودقة',
                          halign='center', color=GRAY, font_size=sp(15)))
        self.body.add_widget(hero)
        for txt, sub, scr in (
                ('تصفية عربية', 'احسب الوزن الصافي لعربية جديدة', 'clear'),
                ('سجل العمليات', 'استعرض وابحث وعدّل العمليات', 'history'),
                ('إعداد أنواع البرانيك', 'أضف الأنواع وأوزانها الفارغة',
                 'settings')):
            c = MenuCard(txt, sub)
            c.bind(on_release=lambda i, s=scr: App.get_running_app().go(s))
            self.body.add_widget(c)

class CrateRow(BoxLayout):
    def __init__(self, page, **kw):
        super().__init__(size_hint_y=None, height=dp(54), spacing=dp(5), **kw)
        self.page = page
        self.tmap = {ar(t['name']): t for t in store().types}
        names = list(self.tmap)
        self.spin = make_spinner(names[0] if names else ar('اختر النوع'), names)
        self.spin.size_hint_x = .42
        self.empty = Num(hint_text='فارغ', size_hint_x=.30)
        self.count = Num(kind='int', hint_text='العدد', size_hint_x=.28)
        self.spin.height = dp(50)
        self.spin.size_hint_y = None
        self.on_type()
        self.spin.bind(text=self.on_type)
        self.empty.bind(text=page.calc)
        self.count.bind(text=page.calc)
        for w in (self.count, self.empty, self.spin):
            self.add_widget(w)

    def on_type(self, *a):
        t = self.tmap.get(self.spin.text)
        self.empty.text = fmt(t['weight']) if t else ''

    def data(self):
        t = self.tmap.get(self.spin.text)
        return {'name': t['name'] if t else '',
                'empty': self.empty.val(), 'count': int(self.count.val())}

class ClearPage(Page):
    title = 'تصفية عربية'

    def build(self):
        self.editing_id = None
        b = self.body
        self.edit_lbl = L('', bold=True, color=EDIT, halign='center', height=0)
        b.add_widget(self.edit_lbl)
        b.add_widget(L('اسم العربية أو صاحبها (اختياري)', bold=True))
        self.name_in = ArInput(hint_text='اكتب اسم العربية أو صاحبها')
        b.add_widget(self.name_in)
        b.add_widget(L('الوزن الإجمالي للعربية (كجم)', bold=True))
        self.gross = Num(hint_text='أدخل الوزن الإجمالي')
        self.gross.bind(text=self.calc)
        b.add_widget(self.gross)
        b.add_widget(L('أنواع البرانيك - حتى 10 أنواع',
                       bold=True, color=GREEN, font_size=sp(19)))

        head = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(5))
        for t, x in (('العدد', .28), ('وزن فارغ', .30), ('النوع', .42)):
            head.add_widget(L(t, halign='center', size_hint_x=x,
                              height=dp(28), font_size=sp(14), color=GRAY))
        b.add_widget(head)
        self.rows_box = BoxLayout(orientation='vertical', size_hint_y=None,
                                  spacing=dp(5))
        self.rows_box.bind(minimum_height=self.rows_box.setter('height'))
        b.add_widget(self.rows_box)
        self.rows = []

        ctl = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        self.del_btn = B('حذف نوع', bg=GRAY, h=50, font_size=sp(16))
        self.add_btn = B('+ إضافة نوع', h=50, font_size=sp(16))
        self.del_btn.bind(on_release=self.del_row)
        self.add_btn.bind(on_release=self.add_row)
        ctl.add_widget(self.del_btn)
        ctl.add_widget(self.add_btn)
        b.add_widget(ctl)

        card = Card(orientation='vertical', bg=(0.91, 0.96, 0.92, 1),
                    size_hint_y=None, height=dp(156), padding=dp(10),
                    spacing=dp(3))
        self.l_cnt = L('', bold=True, color=GREEN)
        self.l_w = L('')
        self.l_net = L('', font_size=sp(22), bold=True, color=DARK,
                       height=dp(48))
        for w in (self.l_cnt, self.l_w, self.l_net):
            card.add_widget(w)
        b.add_widget(card)
        save = B('حفظ العملية', h=62, font_size=sp(22))
        save.bind(on_release=self.save)
        rst = B('تفريغ الشاشة', bg=GRAY, h=50, font_size=sp(17))
        rst.bind(on_release=lambda *a: self.reset())
        b.add_widget(save)
        b.add_widget(rst)
        self.reset()

    def set_edit(self, rec_id):
        self.editing_id = rec_id
        if rec_id:
            self.edit_lbl.set('وضع تعديل عملية محفوظة')
            self.edit_lbl.height = dp(34)
        else:
            self.edit_lbl.set('')
            self.edit_lbl.height = 0

    def load_record(self, rec):
        self.name_in.set_raw(rec.get('name', ''))
        self.rows_box.clear_widgets()
        self.rows = []
        self.gross.text = fmt(rec['gross'])
        for d in (rec.get('rows') or [None])[:10]:
            self.add_row(None, d)
        self.set_edit(rec['id'])

    def on_pre_enter(self, *a):
        if hasattr(self, 'rows'):
            old = [r.data() for r in self.rows]
            self.rows_box.clear_widgets()
            self.rows = []
            for d in old or [None]:
                self.add_row(None, d)

    def on_leave(self, *a):
        if self.editing_id:
            self.reset()

    def add_row(self, inst=None, d=None):
        if len(self.rows) >= 10:
            return
        r = CrateRow(self)
        if d:
            found = False
            for k, t in r.tmap.items():
                if t['name'] == d['name']:
                    r.spin.text = k
                    found = True
            if not found and d['name']:
                k = ar(d['name'])
                r.tmap[k] = {'name': d['name'], 'weight': d['empty']}
                r.spin.values = list(r.tmap)
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
        self.add_btn.disabled = len(self.rows) >= 10
        self.del_btn.disabled = len(self.rows) <= 1

    def totals(self):
        cnt = sum(r.data()['count'] for r in self.rows)
        w = sum(r.data()['count'] * r.data()['empty'] for r in self.rows)
        return cnt, w, self.gross.val() - w

    def calc(self, *a):
        if not getattr(self, 'rows', None):
            return
        cnt, w, net = self.totals()
        self.l_cnt.set('عدد البرانيك: %d' % cnt)
        self.l_w.set('إجمالي وزن البرانيك: %s كجم' % fmt(w))
        self.l_net.set('الوزن الصافي: %s كجم' % fmt(net))
        self.l_net.color = RED if net < 0 else GREEN

    def reset(self):
        self.name_in.set_raw('')
        self.gross.text = ''
        self.rows_box.clear_widgets()
        self.rows = []
        self.add_row()
        self.set_edit(None)

    def save(self, *a):
        gross = self.gross.val()
        cnt, w, net = self.totals()
        if gross <= 0:
            return message('تنبيه', 'أدخل الوزن الإجمالي للعربية')
        if net < 0:
            return message('تنبيه', 'وزن البرانيك أكبر من الوزن الإجمالي')
        rows = [r.data() for r in self.rows if r.data()['count'] > 0]
        if not rows:
            return message('تنبيه', 'أدخل عدد البرانيك أولًا')
        s = store()
        fields = {'name': self.name_in.raw.strip(), 'gross': gross,
                  'rows': rows, 'crates_count': cnt, 'crates_weight': w,
                  'net': net}
        if self.editing_id:
            found = False
            for i, old in enumerate(s.data['records']):
                if old['id'] == self.editing_id:
                    rec = dict(old)
                    rec.update(fields)
                    rec['edited'] = time.strftime('%Y-%m-%d %H:%M')
                    s.data['records'][i] = rec
                    found = True
                    break
            if found:
                s.save()
                message('تم التعديل', 'تم حفظ التعديل. الوزن الصافي: %s كجم'
                        % fmt(net))
                self.reset()
                App.get_running_app().go('history')
                return
        rec = {'id': int(time.time() * 1000),
               'date': time.strftime('%Y-%m-%d %H:%M')}
        rec.update(fields)
        s.data['records'].insert(0, rec)
        s.save()
        message('تم الحفظ', 'تم حفظ العملية. الوزن الصافي: %s كجم' % fmt(net))
        self.reset()

def rec_lines(rec):
    out = ['التاريخ: ' + rec['date']]
    if rec.get('edited'):
        out.append('آخر تعديل: ' + rec['edited'])
    if rec.get('name'):
        out.append('الاسم: ' + rec['name'])
    out.append('الوزن الإجمالي: %s كجم' % fmt(rec['gross']))
    for r in rec['rows']:
        out.append('%s: %d × %s = %s كجم' % (
            r['name'], r['count'], fmt(r['empty']),
            fmt(r['count'] * r['empty'])))
    out.append('إجمالي البرانيك: %d (%s كجم)' % (
        rec['crates_count'], fmt(rec['crates_weight'])))
    out.append('الوزن الصافي: %s كجم' % fmt(rec['net']))
    return out

class RecordCard(TapCard):
    def __init__(self, rec, **kw):
        super().__init__(orientation='horizontal', size_hint_y=None,
                         height=dp(100), padding=[dp(12), dp(8), dp(8), dp(8)],
                         spacing=dp(10), **kw)
        left = BoxLayout(orientation='vertical', size_hint_x=.36)
        left.add_widget(L('الصافي', halign='center', color=GRAY,
                          font_size=sp(13), height=dp(20)))
        left.add_widget(L(fmt(rec['net']), halign='center', bold=True,
                          color=GREEN, font_size=sp(26), height=dp(42)))
        left.add_widget(L('كجم', halign='center', color=GRAY,
                          font_size=sp(13), height=dp(20)))
        right = BoxLayout(orientation='vertical', size_hint_x=.64)
        right.add_widget(L(rec.get('name') or 'بدون اسم', bold=True,
                           font_size=sp(18), height=dp(30)))
        date = rec['date'] + ('  (معدّل)' if rec.get('edited') else '')
        right.add_widget(L(date, color=GRAY, font_size=sp(14), height=dp(24)))
        right.add_widget(L('إجمالي %s كجم  •  %d برنيك' % (
            fmt(rec['gross']), rec['crates_count']),
            font_size=sp(14), height=dp(28)))
        self.add_widget(left)
        self.add_widget(right)
        self.add_widget(AccentBar())

class HistoryPage(Page):
    title = 'سجل العمليات'

    def build(self):
        self.period = 'all'
        self.limit = PAGE_SIZE
        self._ev = None
        b = self.body
        self.search = ArInput(hint_text='ابحث بالاسم أو التاريخ')
        self.search.bind(text=self.on_search)
        b.add_widget(self.search)

        prow = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(5))
        self.pbtns = {}
        for key, label in reversed(PERIODS):
            btn = B(label, bg=GRAY, h=46, font_size=sp(15))
            btn.bind(on_release=lambda i, k=key: self.set_period(k))
            self.pbtns[key] = btn
            prow.add_widget(btn)
        b.add_widget(prow)

        self.sum_box = Card(orientation='vertical', size_hint_y=None,
                            padding=dp(10), spacing=dp(2))
        self.sum_box.bind(minimum_height=self.sum_box.setter('height'))
        b.add_widget(self.sum_box)

        self.list_box = BoxLayout(orientation='vertical', size_hint_y=None,
                                  spacing=dp(8))
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        b.add_widget(self.list_box)

        row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        bk = B('نسخ احتياطي', bg=GREEN2, h=52, font_size=sp(16))
        rs = B('استرجاع', bg=GREEN2, h=52, font_size=sp(16))
        bk.bind(on_release=self.backup)
        rs.bind(on_release=self.restore)
        row.add_widget(rs)
        row.add_widget(bk)
        b.add_widget(row)
        clr = B('مسح كل السجل', bg=RED, h=50, font_size=sp(16))
        clr.bind(on_release=lambda *a: confirm(
            'مسح السجل', 'سيتم حذف كل العمليات. هل أنت متأكد؟', self.clear_all))
        b.add_widget(clr)
        self.mark_period()

    def on_pre_enter(self, *a):
        self.refresh(True)

    def mark_period(self):
        for k, btn in self.pbtns.items():
            c = GREEN if k == self.period else GRAY
            btn._bg = c
            btn.background_color = c

    def set_period(self, key):
        self.period = key
        self.mark_period()
        self.refresh(True)

    def on_search(self, *a):
        if self._ev:
            self._ev.cancel()
        self._ev = Clock.schedule_once(lambda dt: self.refresh(True), .35)

    def filtered(self):
        q = self.search.raw.strip().lower()
        today = time.strftime('%Y-%m-%d')
        month = time.strftime('%Y-%m')
        week = time.strftime('%Y-%m-%d',
                             time.localtime(time.time() - 6 * 86400))
        out = []
        for r in store().data['records']:
            d = r.get('date', '')
            if self.period == 'today' and d[:10] != today:
                continue
            if self.period == 'week' and d[:10] < week:
                continue
            if self.period == 'month' and d[:7] != month:
                continue
            if q:
                hay = ' '.join([d, r.get('name', '')] +
                               [x['name'] for x in r.get('rows', [])]).lower()
                if q not in hay:
                    continue
            out.append(r)
        return out

    def summary(self, recs):
        box = self.sum_box
        box.clear_widgets()
        net = sum(r['net'] for r in recs)
        gross = sum(r['gross'] for r in recs)
        cc = sum(r['crates_count'] for r in recs)
        cw = sum(r['crates_weight'] for r in recs)
        agg = {}
        for r in recs:
            for x in r['rows']:
                c, w = agg.get(x['name'], (0, 0.0))
                agg[x['name']] = (c + x['count'], w + x['count'] * x['empty'])
        box.add_widget(L('ملخص الفترة', bold=True, color=GREEN,
                         font_size=sp(17), height=dp(32)))
        box.add_widget(L('عدد العمليات: %d' % len(recs), height=dp(30),
                         font_size=sp(16)))
        box.add_widget(L('مجموع الصافي: %s كجم' % fmt(net), bold=True,
                         color=DARK, font_size=sp(20), height=dp(40)))
        box.add_widget(L('مجموع الإجمالي: %s كجم' % fmt(gross), height=dp(30),
                         font_size=sp(16)))
        box.add_widget(L('إجمالي البرانيك: %d (%s كجم)' % (cc, fmt(cw)),
                         height=dp(30), font_size=sp(16)))
        for name, (c, w) in agg.items():
            box.add_widget(L('%s: %d (%s كجم)' % (name, c, fmt(w)),
                             color=GRAY, font_size=sp(15), height=dp(28)))

    def refresh(self, reset=False):
        if reset:
            self.limit = PAGE_SIZE
        recs = self.filtered()
        self.summary(recs)
        lb = self.list_box
        lb.clear_widgets()
        if not store().data['records']:
            lb.add_widget(L('لا توجد عمليات سابقة', halign='center',
                            height=dp(70)))
            return
        if not recs:
            lb.add_widget(L('لا توجد عمليات مطابقة', halign='center',
                            height=dp(70)))
            return
        for rec in recs[:self.limit]:
            c = RecordCard(rec)
            c.bind(on_release=lambda i, r=rec: self.show(r))
            lb.add_widget(c)
        rest = len(recs) - self.limit
        if rest > 0:
            more = B('عرض الأقدم (%d متبقية)' % rest, bg=GREEN2, h=50,
                     font_size=sp(16))
            more.bind(on_release=self.show_more)
            lb.add_widget(more)

    def show_more(self, *a):
        self.limit += PAGE_SIZE
        self.refresh()

    def show(self, rec):
        box = BoxLayout(orientation='vertical', spacing=dp(8))
        box.add_widget(lines_view(rec_lines(rec)))
        r1 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        r2 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        close = B('إغلاق', bg=GRAY, h=50, font_size=sp(16))
        dele = B('حذف', bg=RED, h=50, font_size=sp(16))
        edit = B('تعديل', bg=GREEN2, h=50, font_size=sp(16))
        share = B('نسخ كنص', bg=GREEN2, h=50, font_size=sp(16))
        r1.add_widget(close)
        r1.add_widget(dele)
        r2.add_widget(share)
        r2.add_widget(edit)
        box.add_widget(r2)
        box.add_widget(r1)
        p = popup('تفاصيل العملية', box, 540)
        close.bind(on_release=p.dismiss)

        def _del(*a):
            p.dismiss()
            confirm('حذف', 'حذف هذه العملية؟', lambda: self.delete(rec))

        def _edit(*a):
            p.dismiss()
            app = App.get_running_app()
            app.sm.get_screen('clear').load_record(rec)
            app.go('clear')

        def _share(*a):
            try:
                Clipboard.copy('\n'.join(rec_lines(rec)))
            except Exception:
                return message('خطأ', 'تعذر النسخ إلى الحافظة')
            message('تم النسخ', 'تم نسخ التفاصيل. الصقها في واتساب')
        dele.bind(on_release=_del)
        edit.bind(on_release=_edit)
        share.bind(on_release=_share)

    def delete(self, rec):
        store().data['records'] = [r for r in store().data['records']
                                   if r['id'] != rec['id']]
        store().save()
        self.refresh()

    def clear_all(self):
        store().data['records'] = []
        store().save()
        self.refresh(True)

    def backup(self, *a):
        recs = store().data['records']
        if not recs:
            return message('تنبيه', 'لا توجد عمليات لنسخها')
        payload = {'app': 'tasfiya', 'v': 1, 'types': store().types,
                   'records': recs}
        try:
            Clipboard.copy(json.dumps(payload, ensure_ascii=False))
        except Exception:
            return message('خطأ', 'تعذر النسخ إلى الحافظة')
        message('تم النسخ', 'تم نسخ %d عملية. الصق النسخة في واتساب لنفسك '
                'للاحتفاظ بها' % len(recs))

    def restore(self, *a):
        try:
            data = json.loads(Clipboard.paste() or '')
        except Exception:
            data = None
        if (not isinstance(data, dict) or data.get('app') != 'tasfiya'
                or not isinstance(data.get('records'), list)):
            return message('تنبيه', 'انسخ النسخة الاحتياطية أولًا ثم اضغط '
                           'استرجاع')
        need = ('id', 'date', 'gross', 'rows', 'net', 'crates_count',
                'crates_weight')
        ids = {r['id'] for r in store().data['records']}
        new = [r for r in data['records'] if isinstance(r, dict)
               and all(k in r for k in need) and r['id'] not in ids]
        if not new:
            return message('تنبيه', 'كل العمليات موجودة بالفعل')
        confirm('استرجاع', 'سيتم إضافة %d عملية من النسخة الاحتياطية. '
                'متابعة؟' % len(new),
                lambda: self.apply_restore(new, data.get('types')))

    def apply_restore(self, new, types):
        s = store()
        s.data['records'].extend(new)
        s.data['records'].sort(key=lambda r: r['id'], reverse=True)
        if isinstance(types, list):
            names = {t['name'] for t in s.types}
            for t in types:
                try:
                    if t['name'] not in names and float(t['weight']) > 0:
                        s.types.append({'name': t['name'],
                                        'weight': float(t['weight'])})
                        names.add(t['name'])
                except Exception:
                    pass
        s.save()
        self.refresh(True)
        message('تم الاسترجاع', 'تمت إضافة %d عملية' % len(new))

class SettingsPage(Page):
    title = 'إعداد أنواع البرانيك'

    def build(self):
        b = self.body
        b.add_widget(L('اسم كل نوع ووزنه وهو فارغ (كجم):',
                       font_size=sp(16), bold=True))
        head = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(6))
        head.add_widget(Widget(size_hint_x=None, width=dp(56)))
        head.add_widget(L('الوزن الفارغ', halign='center', size_hint_x=.3,
                          height=dp(26), font_size=sp(14), color=GRAY))
        head.add_widget(L('اسم النوع', size_hint_x=.7, height=dp(26),
                          font_size=sp(14), color=GRAY))
        b.add_widget(head)
        self.box = BoxLayout(orientation='vertical', size_hint_y=None,
                             spacing=dp(7))
        self.box.bind(minimum_height=self.box.setter('height'))
        b.add_widget(self.box)
        add = B('+ إضافة نوع جديد', h=52)
        add.bind(on_release=lambda *a: self.add_row('', 0))
        sv = B('حفظ الإعدادات', h=60, font_size=sp(21))
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
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6))
        nm = ArInput(size_hint_x=.7)
        nm.set_raw(name)
        wt = Num(size_hint_x=.3, hint_text='كجم')
        wt.text = fmt(weight) if weight else ''
        dl = B('×', bg=RED, h=50, size_hint=(None, None),
               width=dp(50), font_size=sp(24))
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
        names = set()
        for _, nm, wt in self.rows:
            n = nm.raw.strip()
            if not n:
                continue
            if n in names:
                return message('تنبيه', 'لا تكرر اسم النوع: ' + n)
            if wt.val() <= 0:
                return message('تنبيه', 'أدخل وزنًا صحيحًا للنوع: ' + n)
            names.add(n)
            types.append({'name': n, 'weight': wt.val()})
        if not types:
            return message('تنبيه', 'أضف نوعًا واحدًا على الأقل')
        store().data['types'] = types
        store().save()
        message('تم', 'تم حفظ الإعدادات بنجاح')

class TasfiyaApp(App):
    title = 'تصفية العربيات'

    def build(self):
        self.store = Store(os.path.join(self.user_data_dir, 'data.json'))
        self.sm = ScreenManager(transition=NoTransition())
        for name, cls in (('home', HomePage), ('clear', ClearPage),
                          ('history', HistoryPage), ('settings', SettingsPage)):
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
