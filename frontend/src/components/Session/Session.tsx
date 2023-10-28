import { useDeleteSessionMutation, useGetSessionQuery, useUpdateSessionMutation } from "../../features/courses/sessionApiSlice";
import { useDispatch, useSelector } from "react-redux";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import Breadcrumb from '../Common/Breadcrumb';
import CSELoading from '../Common/CSE/CSELoading';
import CSEOwnerActions from "../Common/CSE/CSEOwnerActions";
import DashboardResultsTable from "../Dashboard/DashboardResultsTable";
import EditableDescription from "../Common/EditableContent/EditableDescription";
import EditableTitle from '../Common/EditableContent/EditableTitle';
import ExerciseContent from "./SessionComponents/ExerciseContent";
import { Tabs } from "../Common/";
import { pushNotification } from "../../features/notification/notificationSlice";
import { selectCurrentUser } from "../../features/auth/authSlice";
import { useTitle } from '../../hooks/useTitle';

const Session = () => {

    const [deleteSession] = useDeleteSessionMutation();
    const [description, setDescription] = useState("");
    const [edit, setEdit] = useState(false);
    const [title, setTitle] = useState("");
    const [updateSession] = useUpdateSessionMutation();
    const { session_id }: any = useParams();
    const dispatch = useDispatch();
    const navigate = useNavigate();
    const username = useSelector(selectCurrentUser);

    const {
        data: session,
        isLoading: sessionIsLoading,
        isSuccess: sessionIsSuccess,
        isError: sessionIsError,
    } = useGetSessionQuery({ id: session_id });

    const course = session?.course;
    const isOwner = session?.course?.owners?.map((o: any) => o.username).includes(username);
    const isTutor = session?.course?.tutors?.map((t: any) => t.username).includes(username);

    useTitle(session?.title);

    useEffect(() => {
        if (sessionIsSuccess) {
            if (session?.title === "" && session?.description === "") {
                setEdit(true);
            }

            setTitle(session?.title);
            setDescription(session?.description);
        }
    }, [session, sessionIsSuccess]);

    const handleUpdate = async () => {
        await updateSession({
            course_id: course?.id,
            id: session?.id,
            title,
            description,
        })
            .unwrap()
            .then(() => {
                dispatch(pushNotification({
                    message: "The session has been updated",
                    type: "success"
                }));
            })
            .catch((e) => {
                dispatch(pushNotification({
                    message: "Something went wrong. The session has not been updated",
                    type: "error"
                }));
            })
    }

    const handleDelete = async (e: any) => {
        e.preventDefault();
        await deleteSession({ id: session_id })
            .unwrap()
            .then(() => {
                dispatch(pushNotification({
                    message: "The session has been deleted",
                    type: "success"
                }));
                navigate(`/course/${course?.id}`);
            })
            .catch((e) => {
                dispatch(pushNotification({
                    message: "Something went wrong. The session has not been deleted",
                    type: "error"
                }));
            })
    }

    if (sessionIsError) {
        return (
            <div className="d-flex align-items-center justify-content-center vh-100 bg-light">
                <h3>The session you are looking for doesn't exist, <br />or you aren't allowed to access it.<br /><a href="/course" className='text-decoration-none'>⬅ Back to courses</a></h3>
            </div>
        )
    }

    const tabs = [
        {
            key: "exercises",
            title: "Exercises",
            content: <ExerciseContent session={session} />,
        },
        {
            key: "results",
            title: "Results",
            content: <DashboardResultsTable sessionId={session_id} />,
        },
    ];

    return sessionIsLoading ? (
        <CSELoading />
    ) : (
        <>
            <div className="container mx-auto">

                <Breadcrumb items={[
                    { link: "/course", title: "Courses" },
                    { link: `/course/${course?.id}`, title: course?.title },
                    { link: null, title: title },
                ]} />

                <br />

                <div className="flex items-center justify-between">
                    <div className="w-full">
                        <EditableTitle
                            edit={edit}
                            isOwner={isOwner}
                            setTitle={setTitle}
                            title={title}
                        />
                    </div>
                    <div className="flex gap-2">
                        <CSEOwnerActions
                            isOwner={isOwner}
                            edit={edit}
                            setEdit={setEdit}
                            handleUpdate={handleUpdate}
                            handleDelete={handleDelete}
                        />
                    </div>
                </div>

                <EditableDescription
                    edit={edit}
                    description={description}
                    isOwner={isOwner}
                    setDescription={setDescription}
                />

                {isOwner || isTutor ? (<>
                    <Tabs tabs={tabs} />
                </>) : (<>
                    <div className='text-xl font-semibold mt-2 md:mt-6'>Exercises</div>
                    <ExerciseContent session={session} />
                </>)}


            </div>
        </>
    )
}

export default Session