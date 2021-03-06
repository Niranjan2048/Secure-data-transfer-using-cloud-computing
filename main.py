import os
import config
from flask import Flask, request, render_template

from secret_database.database import Database
from secret_cryptography.image import Image, ImageLoaderAndSaver, form_secret_key
from secret_cryptography.diffie_hellman_keys import diffie_hellman_shared_key


db = Database()


def start_app():
    app = Flask(__name__)
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.secret_key = "s_ec%re^t#k*ey**su-pe!r"
    return app


app = start_app()


@app.route('/', methods=["GET", "POST"])
def start():
    print("MAIN - {}".format(request.method))
    return render_template("main.html")

@app.route('/gallery')
def gallery():
    return render_template("gallery.html")

@app.route('/contacts', methods=["GET", "POST"])
def contacts(self_name="", new_contact_name=""):
    print("CONTACTS - {} - {}~{}".format(request.method, self_name, new_contact_name))

    if request.method == "POST":

        # new user
        rep_password = request.form.get("new_pass_rep")
        if rep_password:
            user_name, f_name, l_name, password = request.form.get("new_name"),\
                                                  request.form.get("first_name"),\
                                                  request.form.get("last_name"),\
                                                  request.form.get("new_pass")
            if rep_password == password:
                u_info = {"username": user_name, "first_name": f_name, "last_name": l_name, "password": password}
                if db.add_user(u_info):
                    return render_template("contacts.html", contacts=[user_name], self_name=user_name)
            return render_template("main.html", log_msg="", reg_msg="You didn't repeat your password correctly.")

        # log in
        else:
            user_name, password = request.form.get("name"), request.form.get("password")
            if db.check_password(user_name, password):
                return render_template("contacts.html", contacts=db.get_contacts(user_name), self_name=user_name)
            return render_template("main.html", reg_msg="", log_msg="Wrong username or password. Try again.")

    elif request.method == "GET":

        self_name = request.args.get("self_name")
        new_contact_name = request.args.get("new_contact_name")

        if self_name:
            if new_contact_name:
                db.add_contact(self_name, new_contact_name)
            return render_template("contacts.html", contacts=db.get_contacts(self_name), self_name=self_name)

        return render_template("main.html", reg_msg="", log_msg="")


@app.route('/send/<string:from_name>/<string:to_name>', methods=["GET", "POST"])
def send(from_name, to_name):
    print("SEND- {} - {}~{}".format(request.method, from_name, to_name))
    return render_template("send.html", from_name=from_name, to_name=to_name)


@app.route('/result/<string:from_name>/<string:to_name>', methods=["GET", "POST"])
def result(from_name, to_name, read_only=""):
    print("result - {} - {}~{} - ro=".format(request.method, from_name, to_name, read_only))

    fk = db.get_user_info_for_encryption(from_name)["pri_key"]
    tk = db.get_user_info_for_encryption(to_name)["pri_key"]
    sh_key = diffie_hellman_shared_key(fk, tk)

    # send image
    if request.method == "POST":

        try:
            img = request.files["img"]
            img_description = request.form.get("img_description")
            print(img_description)
        except KeyError:
            return render_template("result.html", img_id=None)

        if img is not None:

            # read, encrypt
            img_data = ImageLoaderAndSaver.load_uploaded_image(img)

            the_key = form_secret_key(img_data, sh_key)
            encr_img = Image.encrypt_img(img_data, the_key)

            # save encr image to dropbox in .bmp
            enr_img_id = db.add_picture({"from_user": from_name, "to_user": to_name, "info_from_user": img_description})
            ImageLoaderAndSaver.upload_image_to_filesystem(encr_img, enr_img_id)
            ImageLoaderAndSaver.download_image_from_filesystem(enr_img_id, "./static/")

            # save encr image to 'static' directory of app in .jpg
            img_file_name = str(enr_img_id) + ".jpg"
            img_path = os.path.join(app.static_folder, img_file_name)
            ImageLoaderAndSaver.save_image_locally(encr_img, img_path)
            return render_template("result.html", img_name=str(enr_img_id)+".jpg", from_name=from_name, to_name=to_name, read_only="")
        else:
            return render_template("result.html", img_id=None)

    # read image
    elif request.method == "GET":

        read_only = request.args.get("read_only")
        img_id_list = db.get_not_read_pictures(from_name, to_name)

        print(img_id_list)

        if img_id_list:
            if read_only:
                img_id_list = [db.get_not_read_pictures(from_name, to_name)[-1]]
            for img_id in img_id_list:

                ImageLoaderAndSaver.download_image_from_filesystem(img_id, "./static/")                # download image
                ImageLoaderAndSaver.download_image_from_filesystem(img_id, "./static/")                # download image
                enc_img = ImageLoaderAndSaver.load_image_locally("./static/" + str(img_id) + ".bmp")   # load

                new_the_key = form_secret_key(enc_img, sh_key)                                         # form key
                our_img = Image.decrypt_img(enc_img, new_the_key)
                ImageLoaderAndSaver.save_image_locally(our_img, "./static/" + '_' + str(img_id) + ".jpg")    # save image

                if read_only:
                    db.mark_picture_as_read(img_id)
                    print("marked")
            return render_template("result_receive.html", img_names=list(map(str, img_id_list)), from_name=to_name, to_name=from_name)
        return render_template("result_receive.html", img_names="", from_name=to_name, to_name=from_name)


@app.route('/add_contact/<string:self_name>', methods=["GET", "POST"])
def add_contact(self_name):
    if request.method == "POST":
        new_contact_name = request.form.get("new_contact_name")
        if db.get_general_user_info(new_contact_name):
            return render_template("profile.html", profile_name=new_contact_name, self_name=self_name)
    return render_template("contacts.html", contacts=db.get_contacts(self_name), self_name=self_name)


# if __name__ == '__main__':
#     #app.run(debug=True)
#     app.run()

