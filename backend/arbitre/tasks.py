from celery import shared_task
import json
import requests
import environ
import os
import sys
from rest_framework import status

# Reading .env file
env = environ.Env()
environ.Env.read_env(
    env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
)


def get_lang_id(lang):
    JUDGE0_LANG_IDS = {
        "asm": 45,
        "bash": 46,
        "basic": 47,
        "c": 50,
        "clojure": 86,
        "cobol": 77,
        "commonlisp": 55,
        "cpp": 54,
        "csharp": 51,
        "d": 56,
        "elixir": 57,
        "erlang": 58,
        "executable": 44,
        "fsharp": 87,
        "fortran": 59,
        "go": 60,
        "groovy": 88,
        "haskell": 61,
        "java": 62,
        "javascript": 63,
        "kotlin": 78,
        "lua": 64,
        "objective-c": 79,
        "ocaml": 65,
        "octave": 66,
        "pascal": 67,
        "perl": 85,
        "php": 68,
        "python": 71,
        "r": 80,
        "ruby": 72,
        "rust": 73,
        "scala": 81,
        "sql": 82,
        "swift": 83,
        "typescript": 74,
        "vbnet": 84,
    }
    return JUDGE0_LANG_IDS[lang]


def get_base_url():
    if env("USE_HTTPS", default=True):
        base_url = "https://" + env("HOSTNAME")
    else:
        base_url = "http://" + env("HOSTNAME")
    return base_url


def get_base_api_url():
    return get_base_url() + "/api"


def get_base_runner_url():
    return get_base_url() + "/runner/api"


def get_callback_url():
    if env("DEBUG", default=False):
        return "http://host.docker.internal:8000/runner/api/judge0-callback"
    else:
        return f"{get_base_runner_url()}/judge0-callback"


def get_api_key():
    api_key = env("API_KEY", default="")
    if api_key == "":
        print(
            "API_KEY is not set. The runners can't access the REST API.",
            file=sys.stderr,
        )
        return
    return api_key


def get_test(base_url, test_id):
    tests = requests.get(
        f"{base_url}/test/{test_id}/",
        headers={"Authorization": f"Api-Key {get_api_key()}"},
    )
    if tests.status_code == 401:
        print(
            "ERROR while trying to get tests content : Unauthorized access to the REST API",
            file=sys.stderr,
        )
        return
    return json.loads(tests.content)


def post_testresult_with_token(submission_id, test_id, token, testresult_post_url):
    data = {
        "submission_pk": submission_id,
        "exercise_test_pk": test_id,
        "status": "running",
        "token": token,
    }
    requests.post(
        testresult_post_url,
        data=data,
        headers={"Authorization": f"Api-Key {get_api_key()}"},
    )


def send_test_to_judge0(judge0_url, source_code, additional_files, language_id, stdin):
    request = {
        "language_id": language_id,
        "source_code": source_code,
        "stdin": stdin,
        "callback_url": get_callback_url(),
    }

    if additional_files:
        request["additional_files"] = additional_files

    print("Sending to judge0 with callback_url:", get_callback_url())

    response_object = requests.post(judge0_url, json=request)
    return json.loads(response_object.text)


def post_error_testresult(message, submission_id, test_id, testresult_post_url):
    after_data = {
        "submission_pk": submission_id,
        "exercise_test_pk": test_id,
        "stdout": message,
        "status": "error",
        "time": 0,
        "memory": 0,
    }
    requests.post(
        testresult_post_url,
        data=after_data,
        headers={"Authorization": f"Api-Key {get_api_key()}"},
    )


def zip_directory(path, zip_file_handle):
    for root, _, files in os.walk(path):
        for file in files:
            zip_file_handle.write(
                os.path.join(root, file), os.path.basename(os.path.join(root, file))
            )

    print(f"Directory {path} zipped successfully")


def process_source_single_file(file_content, prefix, suffix):
    # Fix prefix line endings
    if not prefix.endswith("\r") and not prefix.endswith("\n"):
        prefix += "\n"
    source_code = prefix + "\n" + file_content + "\n" + suffix

    return source_code


def process_source_multifile(student_files, exercise_id, submission_id, test_id):
    # student_files is the base64-encoded zip file containing the student's files
    import base64
    import tempfile
    import zipfile
    import os

    teacher_files_request = requests.get(
        f"{get_base_api_url()}/exercise_teacher_files?exercise_id={exercise_id}",
        headers={"Authorization": f"Api-Key {get_api_key()}"},
    )

    # Handle 401 error
    if teacher_files_request.status_code == status.HTTP_401_UNAUTHORIZED:
        raise FileNotFoundError("Unauthorized access to the REST API")

    # Handle 404 error
    if teacher_files_request.status_code == status.HTTP_404_NOT_FOUND:
        testresult_post_url = f"{get_base_runner_url()}/testresult/"
        post_error_testresult(
            "The files required to run tests are missing. Please contact your teacher.",
            submission_id,
            test_id,
            testresult_post_url,
        )
        raise FileNotFoundError("Teacher files not found")

    teacher_files = teacher_files_request.content.decode().replace('"', "")

    student_files_data = base64.b64decode(student_files)
    teacher_files_data = base64.b64decode(teacher_files)

    student_files_zip = tempfile.NamedTemporaryFile(prefix="studentfiles-")
    teacher_files_zip = tempfile.NamedTemporaryFile(prefix="teacherfiles-")

    with open(student_files_zip.name, "wb") as f:
        f.write(student_files_data)

    with open(teacher_files_zip.name, "wb") as f:
        f.write(teacher_files_data)

    with tempfile.TemporaryDirectory(prefix="finaldir-") as tmp:
        # Extract zips in temp folder
        zipfile.ZipFile(teacher_files_zip).extractall(tmp)
        zipfile.ZipFile(student_files_zip).extractall(tmp)

        print("ls : " + str(os.listdir(tmp)))

        # Create final zip file
        final = tempfile.NamedTemporaryFile(prefix="final-")

        # Zip whole tmp directory
        with zipfile.ZipFile(final.name, mode="w") as final_zip:
            zip_directory(tmp, final_zip)
            print("I am now done zipping. This is my content")
            print(final_zip.namelist())

        # Convert zip to b64
        final_b64 = base64.b64encode(final.read())
        final_b64_str = final_b64.decode().replace('"', "")

        final.close()

    student_files_zip.close()
    teacher_files_zip.close()

    return final_b64_str


@shared_task(acks_late=True)
def run_test(
    hostname, exercise_type, submission_id, test_id, file_content, prefix, suffix, lang
) -> None:
    """
    Runs one test on a submission, and stores the result in the database.
    """

    # Arbitre API base URL
    base_url = get_base_runner_url()
    testresult_post_url = f"{base_url}/testresult/"

    try:
        # Get test data from REST API
        test = get_test(base_url, test_id)

        judge0_url = f"http://{hostname}/submissions"

        if exercise_type == "single":
            language_id = get_lang_id(lang)
            source_code = process_source_single_file(file_content, prefix, suffix)
            additional_files = ""
        elif exercise_type == "multiple":
            language_id = 89
            source_code = ""
            additional_files = process_source_multifile(
                file_content, test["exercise"], submission_id, test_id
            )
        else:
            raise Exception("Invalid exercise type")

        response = send_test_to_judge0(
            judge0_url, source_code, additional_files, language_id, test["stdin"]
        )

        if "token" not in response:
            raise requests.exceptions.ConnectionError

        token = response["token"]
        post_testresult_with_token(submission_id, test_id, token, testresult_post_url)

        return
    except requests.exceptions.ConnectionError:
        post_error_testresult(
            "No response from runner. Please contact the administrator.",
            submission_id,
            test_id,
            testresult_post_url,
        )
        return
    except FileNotFoundError as e:
        return
    except Exception as e:
        print("Exception: " + str(e))
        post_error_testresult(
            "An error occured while running the test.",
            submission_id,
            test_id,
            testresult_post_url,
        )
        return


@shared_task(ignore_result=True)
def run_all_pending_testresults() -> None:
    from runner.models import TestResult

    """
    Runs all pending submissions in the database
    """

    TestResult.run_all_pending_testresults()
