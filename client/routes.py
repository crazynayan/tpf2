from typing import List

from flask import render_template, url_for, redirect, flash
from flask_login import login_required

from client import tpf2_app
from server.server import server


@tpf2_app.route('/')
@tpf2_app.route('/index')
@login_required
def home():
    return render_template('home.html')


@tpf2_app.route('/segments')
@login_required
def segments():
    seg_list: List[str] = server.segments()
    if not seg_list:
        flash("Session expired")
        return redirect(url_for('login'))
    return render_template('segments.html', title='Segments', segments=seg_list)


@tpf2_app.route('/segments/<string:seg_name>/instructions')
@login_required
def instructions(seg_name: str):
    ins_list: List[str] = server.instructions(seg_name)
    if not ins_list:
        flash("Session expired")
        return redirect(url_for('login'))
    return render_template('instructions.html', title='Assembly', instructions=ins_list, seg_name=seg_name)


@tpf2_app.route('/macros')
@login_required
def macros():
    macro_list: List[str] = server.macros()
    if not macro_list:
        flash("Session expired")
        return redirect(url_for('login'))
    return render_template('macros.html', title='Data Macro', macros=macro_list)


@tpf2_app.route('/macro/<string:macro_name>/instructions')
@login_required
def symbol_table_view(macro_name: str):
    symbol_table: List[dict] = server.symbol_table(macro_name)
    if not symbol_table:
        flash("Session expired")
        return redirect(url_for('login'))
    return render_template('symbol_table.html', title='Symbol Table', symbol_table=symbol_table, macro_name=macro_name)


@tpf2_app.route('/test_data')
@login_required
def test_data():
    return render_template('home.html')
