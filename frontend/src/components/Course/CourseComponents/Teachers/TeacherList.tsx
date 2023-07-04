import { MinusIcon, PlusIcon, TrashIcon, XMarkIcon } from '@heroicons/react/24/solid';
import { useAddOwnerMutation, useAddTutorMutation, useGetOwnersQuery, useGetTutorsQuery, useRemoveOwnerMutation, useRemoveTutorMutation } from "../../../../features/courses/courseApiSlice"
import { useEffect, useState } from "react";

import { selectCurrentUser } from '../../../../features/auth/authSlice';
import { useGetTeachersQuery } from '../../../../features/users/usersApiSlice';
import { useSelector } from 'react-redux';

const TeacherList = (props: any) => {

    const [addableUsers, setAddableUsers] = useState<any[]>([])
    const [addOwner] = useAddOwnerMutation()
    const [addTutor] = useAddTutorMutation()
    const [owners, setOwners] = useState<any[]>([])
    const [ownerToAdd, setOwnerToAdd] = useState<any>("")
    const [removeOwner] = useRemoveOwnerMutation()
    const [removeTutor] = useRemoveTutorMutation()
    const [tutors, setTutors] = useState<any[]>([])
    const [tutorToAdd, setTutorToAdd] = useState<any>("")
    const course_id: number = props?.courseId
    const current_username = useSelector(selectCurrentUser)
    const isOwner: boolean = props?.isOwner

    const {
        data: ownersData,
        isSuccess: isOwnersSuccess,
    } = useGetOwnersQuery({ course_id })

    const {
        data: tutorsData,
        isSuccess: isTutorsSuccess,
    } = useGetTutorsQuery({ course_id })

    const {
        data: teachersData,
        isSuccess: isTeachersSuccess,
    } = useGetTeachersQuery({})

    useEffect(() => {
        if (isOwnersSuccess) {
            setOwners(ownersData.owners)
        }
    }, [ownersData, isOwnersSuccess])

    useEffect(() => {
        if (isTutorsSuccess) {
            setTutors(tutorsData.tutors)
        }
    }, [tutorsData, isTutorsSuccess])

    useEffect(() => {
        if (isTeachersSuccess && teachersData) {
            const ownersIds = owners.map((o: any) => o.id)
            const tutorsIds = tutors.map((t: any) => t.id)
            setAddableUsers(
                teachersData?.filter((t: any) => !ownersIds.includes(t.id) && !tutorsIds.includes(t.id))
            )
        }
    }, [owners, tutors, teachersData, isTeachersSuccess])

    const handleAddOwner = async (e: any) => {
        e.preventDefault()

        const user_id = teachersData.find((t: any) => t.username === ownerToAdd)?.id
        if (user_id) {
            await addOwner({ course_id, user_id })
            setOwnerToAdd("")
            setOwners([...owners, teachersData.find((t: any) => t.username === ownerToAdd)])
        }
        else if (owners.map((o: any) => o.id).includes(user_id)) {
            alert("User is already an owner")
        }
        else {
            alert("User not found")
        }
    }

    const handleAddTutor = async (e: any) => {
        e.preventDefault()

        const user_id = teachersData.find((t: any) => t.username === tutorToAdd)?.id
        if (user_id) {
            await addTutor({ course_id, user_id })
            setTutorToAdd("")
            setTutors([...tutors, teachersData.find((t: any) => t.username === tutorToAdd)])
        }
        else if (tutors.map((t: any) => t.id).includes(user_id)) {
            alert("User is already a tutor")
        }
        else {
            alert("User not found")
        }
    }

    const handleDeleteOwner = (user_id: number) => {
        removeOwner({ course_id: course_id, user_id: user_id })
        setOwners(owners.filter((o: any) => o.id !== user_id))
    }

    const handleDeleteTutor = (user_id: number) => {
        removeTutor({ course_id: course_id, user_id: user_id })
        setTutors(tutors.filter((t: any) => t.id !== user_id))
    }

    return isOwnersSuccess && isTeachersSuccess ? (
        <div className="flex flex-wrap mt-6">
            <div className="w-full md:w-1/2 p-0 md:pr-6 md:border-r">
                <div className="p-1">
                    <h2 className="text-2xl font-bold">Owners</h2>
                    <p className="text-gray-600">Owners manage the sessions and exercises for this course. They also manage students and view their results.</p>
                    <ul className="mt-4">
                        {owners.map((owner: any) => (
                            <li key={owner.id} className="flex items-center justify-between font-medium py-2 pl-4 pr-2 mt-2 first:mt-0 bg-gray-50 hover:bg-gray-100 border rounded-md">
                                {owner.username}
                                {isOwner ? (
                                    owner.username !== current_username ? (
                                        <XMarkIcon className="text-red-500 border rounded-md bg-gray-100 hover:bg-gray-200 text-secondary cursor-pointer w-6 h-6" onClick={() => handleDeleteOwner(owner.id)} />
                                    ) : (
                                        <XMarkIcon className="text-gray-400 border rounded-md bg-gray-200 text-secondary cursor-default w-6 h-6" data-toggle="tooltip" title="You cannot remove yourself." />
                                    )
                                ) : null}
                            </li>
                        ))}
                        {isOwner && (
                            <li className="flex items-center justify-between mt-2 w-full">
                                <form onSubmit={handleAddOwner} className="flex items-center w-full">
                                    <input
                                        type="text"
                                        placeholder="Add owner"
                                        list="teacherOptions"
                                        value={ownerToAdd}
                                        onChange={(e: any) => setOwnerToAdd(e.target.value)}
                                        className="border border-gray-300 rounded-lg py-2 px-4 mr-2 focus:outline-none focus:border-blue-500 w-full"
                                    />
                                    <datalist id="teacherOptions">
                                        {addableUsers && addableUsers.map((user: any) => (
                                            <option key={user.id} value={user.username} />
                                        ))}
                                    </datalist>
                                    <PlusIcon
                                        aria-label='Add owner'
                                        className={`${ownerToAdd ? "text-gray-500 bg-gray-50 hover:bg-gray-100" : "text-gray-300 bg-gray-100"} w-10 h-10 p-1 border rounded-md`}
                                        onClick={handleAddOwner}
                                        role="button"
                                        type="submit"
                                    />
                                </form>
                            </li>
                        )}
                    </ul>
                </div>
            </div>
            <div className="w-full md:w-1/2 p-0 md:pl-1 mt-6 md:mt-0">
                <div className="p-1 md:pl-6">
                    <h2 className="text-2xl font-bold">Tutors</h2>
                    <p className="text-gray-600">Tutors can manage students and see their results.</p>
                    <ul className="mt-4">
                        {tutors.map((tutor: any) => (
                            <li key={tutor.id} className="flex items-center justify-between font-medium py-2 pl-4 pr-2 mt-2 first:mt-0 bg-gray-50 hover:bg-gray-100 border rounded-md">
                                {tutor.username}
                                {isOwner ? (
                                    tutor.username !== current_username ? (
                                        <XMarkIcon className="text-red-500 border rounded-md bg-gray-100 hover:bg-gray-200 text-secondary cursor-pointer w-6 h-6" onClick={() => handleDeleteTutor(tutor.id)} />
                                    ) : (null)
                                ) : null}
                            </li>
                        ))}
                        {isOwner && (
                            <li className="flex items-center justify-between mt-2 w-full">
                                <form onSubmit={handleAddTutor} className="flex items-center w-full">
                                    <input
                                        type="text"
                                        placeholder="Add tutor"
                                        list="teacherOptions"
                                        value={tutorToAdd}
                                        onChange={(e: any) => setTutorToAdd(e.target.value)}
                                        className="border border-gray-300 rounded-lg py-2 px-4 mr-2 focus:outline-none focus:border-blue-500 w-full"
                                    />
                                    <datalist id="teacherOptions">
                                        {addableUsers && addableUsers.map((user: any) => (
                                            <option key={user.id} value={user.username} />
                                        ))}
                                    </datalist>
                                    <PlusIcon
                                        aria-label='Add tutor'
                                        className={`${tutorToAdd ? "text-gray-500 bg-gray-50 hover:bg-gray-100" : "text-gray-300 bg-gray-100"} w-10 h-10 p-1 border rounded-md`}
                                        onClick={handleAddTutor}
                                        role="button"
                                        type="submit"
                                    />
                                </form>
                            </li>
                        )}
                    </ul>
                </div>
            </div>
        </div>
    ) : null;
}

export default TeacherList