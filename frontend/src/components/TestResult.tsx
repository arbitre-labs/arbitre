import { Badge, ListGroup, Spinner } from 'react-bootstrap';
import { useGetSubmissionByExerciseQuery, useGetSubmissionTestResultsQuery } from '../features/submission/submissionApiSlice'

const TestResult = (props: any) => {

    const exercise_id = props.exercise_id;
    const user_id = props.user_id || null;

    const {
        data: testResults,
        isSuccess,
    } = useGetSubmissionTestResultsQuery({ exercise_id: exercise_id, user_id: user_id });

    const {
        data: submissionData,
    } = useGetSubmissionByExerciseQuery({ exercise_id: exercise_id });

    console.log(submissionData)

    const testResultContent = (result: any) => {
        if (result.running) {
            return <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        } else {
            return <span className="font-monospace">{result.stdout}</span>
        }
    }

    const statusPillContent = (result: any) => {
        if (result.status === "running") {
            return (<>
                <span className="spinner-border spinner-border-sm p-1 m-1" role="status" aria-hidden="true"></span>
            </>)
        }
        else if (result.status === "pending") {
            return (<>
                <Badge bg="secondary">Pending</Badge>
            </>)
        }
        else if (result.status === "success") {
            return (<>
                <Badge bg="secondary">{result.time} s</Badge>
                &nbsp;
                <Badge bg="success">Success</Badge>
            </>)
        }
        else if (result.status === "failed") {
            return (<>
                <Badge bg="secondary">Fail</Badge>
            </>)
        }
        else if (result.status === "error") {
            return (<>
                <Badge bg="danger">Error</Badge>
            </>)
        }
    }

    const statusContent = (status: string) => {
        if (status === "running") {
            return (
                <Spinner animation="border" role="status" as="span" size="sm">
                    <span className="visually-hidden">Running...</span>
                </Spinner>
            )
        }
        else if (status === "PENDING" || status === "pending") {
            return (
                <Spinner animation="border" role="status" as="span" size="sm">
                    <span className="visually-hidden">Pending...</span>
                </Spinner>
            )
        }
        else if (status === "success") {
            return <Badge bg="success">Success</Badge>
        }
        else if (status === "failed") {
            return <Badge bg="secondary">Fail</Badge>
        }
        else if (status === "error") {
            return <Badge bg="danger">Error</Badge>
        }
    }

    return (submissionData && submissionData.length > 0 && isSuccess && testResults) ? (
        <ListGroup>
            <ListGroup.Item className={'bg-light d-flex justify-content-between align-items-start'}>
                <span className='fw-bold'>{submissionData[0]?.file?.split("/").pop()}</span>
                {statusContent(submissionData[0].status)}
            </ListGroup.Item>

            {testResults.map((result: any, i: number) => (
                <ListGroup.Item className='d-flex justify-content-between align-items-start' key={i}>
                    <div className='ms-2 me-auto'>
                        <div className="fw-bold">{result.exercise_test.name}</div>
                        {testResultContent(result)}
                    </div>
                    {statusPillContent(result)}
                </ListGroup.Item>
            ))}

        </ListGroup>
    ) : (<>
        <p className='text-danger'>There was an error while trying to display the test results.</p>
        <p>Try submitting the file again.</p>
    </>)
}

export default TestResult