// import '../../join-code.css'

import { useEffect, useState } from 'react'

import { ChevronLeftIcon } from '@heroicons/react/24/solid'
import Header from '../Common/Header'
import { Link } from "react-router-dom";
import { pushNotification } from '../../features/notification/notificationSlice';
import useDigitInput from 'react-digit-input';
import { useDispatch } from 'react-redux';
import { useJoinCourseWithCodeMutation } from '../../features/courses/courseApiSlice';
import { useNavigate } from 'react-router-dom';
import { useParams } from 'react-router-dom'

const JoinCourse = (props: any) => {

    const navigate = useNavigate()
    const dispatch = useDispatch()
    const { join_code: join_code_parameter } = useParams<{ join_code: string }>()
    const [joinCourseWithCode] = useJoinCourseWithCodeMutation()
    const [err, setErr] = useState<any>("")
    const [codeInput, setCodeInput] = useState<any>('')

    const handleCodeInput = (value: any) => {
        setErr("")
        setCodeInput(value.toUpperCase())
    }

    const digits = useDigitInput({
        acceptedCharacters: /^[a-zA-Z0-9]$/,
        length: 8,
        value: codeInput,
        onChange: handleCodeInput,
    });

    const handleSubmit = async (e: any) => {

        e.preventDefault()

        try {
            setCodeInput(codeInput.toUpperCase())
            const response = await joinCourseWithCode({ join_code: codeInput }).unwrap()
            dispatch(pushNotification({
                message: "You have successfully joined the course.",
                type: "success"
            }))
            navigate(`/course/${response.course_id}`)

        } catch (err: any) {
            if (err.data.course_id) {
                dispatch(pushNotification({
                    message: "You are already in this course.",
                    type: "warning"
                }))
                navigate(`/course/${err.data.course_id}`)
                return
            }
            setErr(err.data.message)
        }
    }

    useEffect(() => {

        async function joinCourse(code: string) {
            try {
                setCodeInput(code.toUpperCase())
                const response = await joinCourseWithCode({ join_code: code }).unwrap()
                navigate(`/course/${response.course_id}`)
            } catch (err: any) {
                if (err.data.course_id) {
                    navigate(`/course/${err.data.course_id}`)
                    return
                }
                setErr(err.data.message)
            }
        }


        if (join_code_parameter) {

            if (join_code_parameter.length !== 8) {
                setErr("Invalid join link.")
                navigate("/course/join")
                return
            }
            setCodeInput(join_code_parameter)

            joinCourse(join_code_parameter)

        }
    }, [join_code_parameter, joinCourseWithCode, navigate])

    return (
        <>
            <Header />

            <br />
            <br />

            <div className="container mx-auto">
                <Link to="/course" className="inline-flex bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline items-center my-4 md:my-6">
                    <ChevronLeftIcon className="h-5 w-5" />
                    Back to courses
                </Link>

                <div className="bg-gray-50 rounded-xl md:rounded-3xl border shadow-gray-400/50 p-4 md:p-6 md:h-auto h-5/6 flex flex-col items-center justify-center">

                    <h1 className="text-4xl font-bold mb-4 text-gray-700">Join a course</h1>
                    <hr />
                    {err === '' ? (
                        <p className="text-gray-600 m-2">Enter the 8 character course code to join a course.</p>
                    ) : (
                        <p className="text-red-500 m-2">{err}</p>
                    )}

                    <form className="m-2 md:n-4 bg-gray-100 border rounded-xl md:rounded-3xl shadow-sm shadow-gray-400/50  p-4 md:p-6 overflow-x-auto flex justify-center">
                        {Array(8)
                            .fill(0)
                            .map((_, i) => (
                                <input
                                    type="text"
                                    placeholder="X"
                                    key={i}
                                    autoFocus={i === 0}
                                    className="font-mono w-8 mx-1 text-gray-700 placeholder-gray-300 border border-gray-300 rounded-md text-4xl text-center focus:placeholder:opacity-0 caret-transparent"
                                    {...digits[i]}
                                    onChange={(e) => handleCodeInput(e.target.value)}
                                />
                            ))}
                    </form>

                    <br />

                    <button
                        className={`${codeInput.replace(' ', '').length === 8 ? " text-gray-50 bg-gray-500 hover:bg-gray-700" : "text-gray-100 bg-gray-300"} font-bold py-2 px-4 transition duration-300 rounded-lg justify-center flex items-center`}
                        disabled={codeInput.replace(' ', '').length < 8}
                        onClick={handleSubmit}
                    >
                        Join
                    </button>
                </div>
            </div>
        </>
    )
}

export default JoinCourse