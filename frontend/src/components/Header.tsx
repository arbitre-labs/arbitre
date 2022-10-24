import React from 'react'
import store from '../app/store'
import { Container, Dropdown, DropdownButton, Navbar } from 'react-bootstrap'
import { useLogoutMutation } from '../features/auth/authApiSlice'
import { useNavigate } from 'react-router-dom'
import { logOut } from '../features/auth/authSlice'
import { useDispatch } from 'react-redux'


const Header = () => {

    const username = store.getState().auth?.user

    const [ logout ] = useLogoutMutation()
    const dispatch = useDispatch()
    const navigate = useNavigate()

    const signout = () => {
        const refresh = store.getState().auth?.refreshToken
        logout({refresh})
        dispatch(logOut({}))
        navigate('/')
    }

    return (
        <Navbar className="py-3 border-bottom">
            <Container>
                <Navbar.Brand href={"/"} className="fw-bold">Arbitre</Navbar.Brand>
                <DropdownButton title={username} align="end">
                        <Dropdown.Item href="/courses">Courses</Dropdown.Item>
                        <Dropdown.Item href="/exercises">Submissions</Dropdown.Item>
                        <Dropdown.Divider />
                        <Dropdown.Item as="button" onClick={signout}>Sign Out</Dropdown.Item>
                </DropdownButton>
            </Container>
        </Navbar>
    )
}

export default Header