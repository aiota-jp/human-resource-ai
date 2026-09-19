"""Flaskアプリケーション エントリーポイント"""
import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.utils import secure_filename
from config import Config
from database import init_db
from services.auth_service import authenticate, ensure_default_users, login_required, roles_required
from services.employee_service import get_all_employees, get_employee_by_id, create_employee, update_employee, delete_employee
from services.training_service import get_all_trainings, get_training_by_id, create_training, get_training_histories, upsert_training_history
from services.evaluation_service import get_evaluation_targets, save_evaluation
from services.dify_service import generate_evaluation_comment
from services.excel_service import allowed_file, import_employee_excel, import_training_excel, export_evaluation_excel
from services.report_service import get_reports, create_report
from services.search_service import search_documents, send_chat_message

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)
init_db()
ensure_default_users()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = authenticate(request.form.get("username", ""), request.form.get("password", ""))
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("ログインしました", "success")
            return redirect(url_for("index"))
        flash("ユーザーIDまたはパスワードが違います", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("ログアウトしました", "info")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/employees")
@login_required
@roles_required("staff", "admin")
def employee_list():
    keyword = request.args.get("keyword", "")
    return render_template("employee_list.html", employees=get_all_employees(keyword))


@app.route("/employees/new", methods=["GET", "POST"])
@login_required
@roles_required("staff", "admin")
def employee_new():
    if request.method == "POST":
        create_employee(request.form.to_dict())
        flash("社員を登録しました", "success")
        return redirect(url_for("employee_list"))
    return render_template("employee_form.html", employee=None)


@app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("staff", "admin")
def employee_edit(employee_id):
    employee = get_employee_by_id(employee_id)
    if not employee:
        flash("社員が見つかりません", "warning")
        return redirect(url_for("employee_list"))
    if request.method == "POST":
        update_employee(employee_id, request.form.to_dict())
        flash("社員情報を更新しました", "success")
        return redirect(url_for("employee_list"))
    return render_template("employee_form.html", employee=employee)


@app.route("/employees/<int:employee_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def employee_delete(employee_id):
    delete_employee(employee_id)
    flash("社員を削除しました", "success")
    return redirect(url_for("employee_list"))


@app.route("/trainings")
@login_required
@roles_required("staff", "admin")
def training_list():
    return render_template("training_list.html", trainings=get_all_trainings())


@app.route("/trainings/new", methods=["GET", "POST"])
@login_required
@roles_required("staff", "admin")
def training_new():
    if request.method == "POST":
        create_training(request.form.to_dict())
        flash("研修を登録しました", "success")
        return redirect(url_for("training_list"))
    return render_template("training_form.html", training=None)


@app.route("/trainings/<int:training_id>/history", methods=["GET", "POST"])
@login_required
@roles_required("staff", "admin")
def training_history(training_id):
    training = get_training_by_id(training_id)
    if not training:
        flash("研修が見つかりません", "warning")
        return redirect(url_for("training_list"))
    if request.method == "POST":
        for emp_id in request.form.getlist("employee_id"):
            upsert_training_history(int(emp_id), training_id, {
                "attendance_rate": request.form.get(f"attendance_rate_{emp_id}"),
                "understanding_level": request.form.get(f"understanding_level_{emp_id}"),
                "report_score": request.form.get(f"report_score_{emp_id}"),
            })
        flash("研修履歴を保存しました", "success")
        return redirect(url_for("training_history", training_id=training_id))
    return render_template("training_history.html", training=training, histories=get_training_histories(training_id))


@app.route("/evaluations")
@login_required
@roles_required("staff", "admin")
def evaluation_list():
    return render_template("evaluation.html", evaluations=get_evaluation_targets())


@app.route("/evaluations/<int:employee_id>/generate", methods=["POST"])
@login_required
@roles_required("staff", "admin")
def evaluation_generate(employee_id):
    target = next((e for e in get_evaluation_targets() if e["employee_id"] == employee_id), None)
    if not target:
        flash("評価対象が見つかりません", "warning")
        return redirect(url_for("evaluation_list"))
    comment = generate_evaluation_comment(
        target["name"], target["understanding_level"], target["attendance_rate"], target["report_score"]
    )
    save_evaluation(employee_id, target["calculated_score"], comment)
    flash("AI評価コメントを生成しました", "success")
    return redirect(url_for("evaluation_list"))


@app.route("/import", methods=["GET", "POST"])
@login_required
@roles_required("staff", "admin")
def import_excel():
    trainings = get_all_trainings()
    if request.method == "POST":
        file = request.files.get("file")
        import_type = request.form.get("import_type")
        if not file or file.filename == "":
            flash("ファイルを選択してください", "warning")
            return redirect(url_for("import_excel"))
        if not allowed_file(file.filename):
            flash("xlsx または csv を指定してください", "danger")
            return redirect(url_for("import_excel"))
        path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file.filename))
        file.save(path)
        if import_type == "training":
            count, errors = import_training_excel(path, int(request.form.get("training_id") or 0))
        else:
            count, errors = import_employee_excel(path)
        flash(f"{count}件取り込みました", "success")
        for error in errors[:5]:
            flash(error, "warning")
        return redirect(url_for("import_excel"))
    return render_template("import.html", trainings=trainings)


@app.route("/export")
@login_required
@roles_required("staff", "admin")
def export_excel():
    output_path = os.path.join(app.config["OUTPUT_FOLDER"], f"evaluation_{date.today().isoformat()}.xlsx")
    export_evaluation_excel(get_evaluation_targets(), output_path)
    return send_file(output_path, as_attachment=True)


@app.route("/reports", methods=["GET", "POST"])
@login_required
def report_list():
    if request.method == "POST":
        create_report(request.form.to_dict())
        flash("日報を登録しました", "success")
        return redirect(url_for("report_list"))
    return render_template("report.html", reports=get_reports(), employees=get_all_employees(), today=date.today().isoformat())


@app.route("/reports/new")
@login_required
def report_new():
    return redirect(url_for("report_list"))


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    result = None
    question = ""
    if request.method == "POST":
        question = request.form.get("question", "")
        result = search_documents(question)
    return render_template("search.html", result=result, question=question)


@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    messages = session.get("chat_messages", [])
    if request.method == "POST":
        message = request.form.get("message", "")
        response = send_chat_message(message, session.get("conversation_id", ""))
        session["conversation_id"] = response.get("conversation_id", "")
        messages.append({"role": "user", "text": message})
        messages.append({"role": "assistant", "text": response.get("answer", "")})
        session["chat_messages"] = messages[-20:]
        return redirect(url_for("chat"))
    return render_template("chat.html", messages=messages)


if __name__ == "__main__":
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=5000)
