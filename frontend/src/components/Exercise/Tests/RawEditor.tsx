import { useDispatch } from "react-redux";
import { useEffect, useState } from "react";

import { Editor } from "@monaco-editor/react";
import RawEditorHelp from "./RawEditorHelp";
import { pushNotification } from "../../../features/notification/notificationSlice";
import { useGetTestsOfExerciseQuery } from "../../../features/courses/testApiSlice";
import { useUploadRawTestsMutation } from "../../../features/courses/testApiSlice";

interface Test {
  id: number;
  exercise: number;
  name: string;
  stdin: string;
  stdout: string;
  coefficient: number;
}

const RawEditor = (props: { exercise_id: number, isOwner: boolean }) => {
  const { data: tests, isSuccess: testsSuccess } = useGetTestsOfExerciseQuery({
    exercise_id: props.exercise_id,
  });

  const [rawTestsString, setRawTestsString] = useState("");
  const [uploadRawTests] = useUploadRawTestsMutation();
  const dispatch = useDispatch();

  useEffect(() => {
    if (!testsSuccess) return;

    const cleanedTestsObject = tests.map((test: Test) => ({
      name: test.name,
      stdin: test.stdin,
      stdout: test.stdout,
    }));

    setRawTestsString(JSON.stringify(cleanedTestsObject, null, 4));
  }, [tests, testsSuccess]);

  const handleUpload = () => {
    uploadRawTests({
      exercise_id: props.exercise_id,
      raw_tests: rawTestsString.replace(/(\r\n|\n|\r)/gm, ""),
    })
      .unwrap()
      .then(() => {
        // set test as not new, with new id
        dispatch(
          pushNotification({
            message: "Tests uploaded successfully",
            type: "success",
          })
        );
      })
      .catch(() => {
        dispatch(
          pushNotification({
            message:
              "There was an error creating the tests. Please check the JSON data.",
            type: "error",
          })
        );
      });
  };

  return (
    <div className="pt-2">
      <RawEditorHelp />
      <Editor
        height="40vh"
        defaultLanguage="json"
        value={rawTestsString}
        onChange={(value: any, _: any) => setRawTestsString(value)}
        options={{
          minimap: { enabled: false },
          lineNumbers: "on",
          renderFinalNewline: "off",
          renderValidationDecorations: "on",
          scrollBeyondLastLine: false,
          scrollbar: {
            vertical: "hidden",
            alwaysConsumeMouseWheel: false,
          },
          readOnly: !props.isOwner,
          readOnlyMessage: { value: "Only owners can edit tests" }
        }}
      />
      <button
        className={`flex items-center gap-2 text-primary text-sm
            bg-blue-50 hover:bg-blue-100 text-blue-500 border border-blue-200
        font-semibold py-2 px-4 rounded-lg transition-all mt-2`}
        onClick={handleUpload}
      >
        Save tests
      </button>
    </div>
  );
};

export default RawEditor;
