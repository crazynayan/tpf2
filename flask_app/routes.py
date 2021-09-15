from typing import List

from flask import render_template, redirect, url_for
from flask_login import current_user

from flask_app import tpf2_app
from flask_app.server import Server
from flask_app.user import cookie_login_required


@tpf2_app.route("/")
@tpf2_app.route("/index")
def home():
    return render_template("home.html")


@tpf2_app.route("/segments")
@cookie_login_required
def segments():
    seg_list: List[str] = Server.segments()
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    return render_template("segments.html", title="Segments", segments=seg_list)


@tpf2_app.route("/segments/<string:seg_name>/instructions")
@cookie_login_required
def instructions(seg_name: str):
    response: dict = Server.instructions(seg_name)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    return render_template("instructions.html", title="Assembly", instructions=response["formatted_instructions"],
                           seg_name=seg_name, not_supported_instructions=response["formatted_not_supported"])


@tpf2_app.route("/macros")
@cookie_login_required
def macros():
    macro_list: List[str] = Server.macros()
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    return render_template("macros.html", title="Data Macro", macros=macro_list)


@tpf2_app.route("/macro/<string:macro_name>/instructions")
@cookie_login_required
def symbol_table_view(macro_name: str):
    symbol_table: List[dict] = Server.symbol_table(macro_name)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    return render_template("symbol_table.html", title="Symbol Table", symbol_table=symbol_table, macro_name=macro_name)
