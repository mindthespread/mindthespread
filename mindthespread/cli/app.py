# from importlib.resources import files
# import dotenv
# import subprocess
# from streamlit.web import bootstrap
#
#
# def main():
#     dotenv.load_dotenv()
#     app_path = files('mts.app')
#     # subprocess.run(["streamlit", "run", app_path.joinpath('Mind_The_Spread.py')])
#
#     real_script = f"{app_path}/Mind_The_Spread.py"
#     bootstrap.run(real_script, is_hello=False, args=[], flag_options={})
#
#
# if __name__ == '__main__':
#     main()