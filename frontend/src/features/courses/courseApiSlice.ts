import { apiSlice } from "../../app/api/apiSlice";

export const courseApiSlice = apiSlice.injectEndpoints({
    endpoints: builder => ({
        getCourse: builder.query({
            query: params => ({
                url: `/api/course/${params.id}/`,
                method: 'GET',
            })
        }),
        getAllCourses: builder.query({
            query: params => ({
                url: `/api/course/`,
                method: 'GET',
            })
        }),
        getCoursesSessionsExercises: builder.query({
            query: params => ({
                url: `/api/courses_sessions_exercises/`,
                method: 'GET',
            })
        }),
        createCourse: builder.mutation({
            query: (data: any) => {
                return (
                    {
                        url: '/api/course/',
                        method: 'POST',
                        credentials: 'include',
                        body: data //Must include : title, description. Optional fields : students
                    }
                )
            }
        }),
        updateCourse: builder.mutation({
            query: (data: any) => {
                return (
                    {
                        url: `/api/course/${data.id}/`,
                        method: 'PUT',
                        credentials: 'include',
                        body: data //Must include : title, description. Optional fields : students
                    }
                )
            }
        }),
        deleteCourse: builder.mutation({
            query: (id: any) => {
                return (
                    {
                        url: `/api/course/${id}/`,
                        method: 'DELETE',
                        credentials: 'include',
                    }
                )
            }
        }),
        getOwners: builder.query({
            query: params => ({
                url: `/api/course_owner?course_id=${params.course_id}`,
                method: 'GET',
            })
        }),
        addOwner: builder.mutation({
            query: (data: any) => ({
                url: `/api/course_owner/`,
                method: 'POST',
                credentials: 'include',
                body: data //Must include : course_id, user_id
            })
        }),
        removeOwner: builder.mutation({
            query: (data: any) => ({
                url: `/api/course_owner/${data.course_id}/`,
                method: 'DELETE',
                credentials: 'include',
                body: { user_id: data.user_id } //Must include : course_id, user_id
            })
        }),
        getTutors: builder.query({
            query: params => ({
                url: `/api/course_tutor?course_id=${params.course_id}`,
                method: 'GET',
            })
        }),
        addTutor: builder.mutation({
            query: (data: any) => ({
                url: `/api/course_tutor/`,
                method: 'POST',
                credentials: 'include',
                body: data //Must include : course_id, user_id
            })
        }),
        removeTutor: builder.mutation({
            query: (data: any) => ({
                url: `/api/course_tutor/${data.course_id}/`,
                method: 'DELETE',
                credentials: 'include',
                body: { user_id: data.user_id } //Must include : course_id, user_id
            })
        }),
        getStudents: builder.query({
            query: params => ({
                url: `/api/course_student?course_id=${params.course_id}`,
                method: 'GET',
            })
        }),
        addStudent: builder.mutation({
            query: (data: any) => ({
                url: `/api/course_student/`,
                method: 'POST',
                credentials: 'include',
                body: data //Must include : course_id, user_id
            })
        }),
        removeStudent: builder.mutation({
            query: (data: any) => ({
                url: `/api/course_student/${data.course_id}/`,
                method: 'DELETE',
                credentials: 'include',
                body: { user_id: data.user_id }
            })
        }),
        updateLanguage: builder.mutation({
            query: (data: any) => ({
                url: `/api/course/${data.course_id}/`,
                method: 'PATCH',
                credentials: 'include',
                body: { language: data.language }
            })
        }),
        joinCourseWithCode: builder.mutation({
            query: (data: any) => ({
                url: `/api/course_join/`,
                method: 'POST',
                credentials: 'include',
                body: data //Must include : join_code
            })
        }),
        refreshJoinCode: builder.mutation({
            query: (data: any) => ({
                url: `/api/course_refresh_code/`,
                method: 'POST',
                credentials: 'include',
                body: data //Must include : course_id
            })
        }),
        setJoinCodeEnabled: builder.mutation({
            query: (data: any) => ({
                url: `/api/course_join_code_enabled/`,
                method: 'POST',
                credentials: 'include',
                body: data //Must include : course_id, enabled
            })
        }),
        getCourseStudentGroups: builder.query({
            query: params => ({
                url: `/api/student_group?course_id=${params.course_id}`,
                method: 'GET',
            })
        }),
        setGroupsEnabled: builder.mutation({
            query: (data: any) => ({
                url: `/api/course/${data.course_id}/`,
                method: 'PATCH',
                credentials: 'include',
                body: { groups_enabled: data.groups_enabled }
            })
        }),
        setAutoGroups: builder.mutation({
            query: (data: any) => ({
                url: `/api/course/${data.course_id}/`,
                method: 'PATCH',
                credentials: 'include',
                body: {
                    auto_groups_enabled: data.auto_groups_enabled,
                    auto_groups_type: data.auto_groups_type,
                    auto_groups_number: data.auto_groups_number,
                }
            })
        }),
        setStudentGroup: builder.mutation({
            query: (data: any) => ({
                url: `/api/set_student_group/`,
                method: 'POST',
                credentials: 'include',
                body: {
                    user_id: data.user_id,
                    student_group: data.student_group,
                }
            })
        }),
    })
})

export const {
    useAddOwnerMutation,
    useAddStudentMutation,
    useAddTutorMutation,
    useCreateCourseMutation,
    useDeleteCourseMutation,
    useGetAllCoursesQuery,
    useGetCourseQuery,
    useGetCoursesSessionsExercisesQuery,
    useGetCourseStudentGroupsQuery,
    useGetOwnersQuery,
    useGetStudentsQuery,
    useGetTutorsQuery,
    useJoinCourseWithCodeMutation,
    useRefreshJoinCodeMutation,
    useRemoveOwnerMutation,
    useRemoveStudentMutation,
    useRemoveTutorMutation,
    useSetAutoGroupsMutation,
    useSetGroupsEnabledMutation,
    useSetJoinCodeEnabledMutation,
    useSetStudentGroupMutation,
    useUpdateCourseMutation,
    useUpdateLanguageMutation,
} = courseApiSlice;