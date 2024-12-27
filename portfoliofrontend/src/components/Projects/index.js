import React from 'react'
import { useState } from 'react'
import { Container, Wrapper, Title, Desc, CardContainer, ToggleButtonGroup, ToggleButton, Divider } from './ProjectsStyle'
import ProjectCard from '../Cards/ProjectCards'
import { projects } from '../../data/constants'


const Projects = ({openModal,setOpenModal}) => {
  const [toggle, setToggle] = useState('all');
  return (
    <Container id="projects">
      <Wrapper>
        <Title>Projects</Title>
        <Desc>
          I have worked on a wide range of projects. To check the detailed, click each project! For login, sign up or ID: admin / PW: password
        </Desc>
        <ToggleButtonGroup >
          {toggle === 'all' ?
            <ToggleButton active value="all" onClick={() => setToggle('all')}>All</ToggleButton>
            :
            <ToggleButton value="all" onClick={() => setToggle('all')}>All</ToggleButton>
          }
          <Divider />
          {toggle === 'REST API' ?
            <ToggleButton active value="REST API" onClick={() => setToggle('REST API')}>REST API</ToggleButton>
            :
            <ToggleButton value="REST API" onClick={() => setToggle('REST API')}>REST API</ToggleButton>
          }
          <Divider />
          {toggle === 'ERP Dashboard' ?
            <ToggleButton active value="ERP Dashboard" onClick={() => setToggle('ERP Dashboard')}>ERP Dashboard</ToggleButton>
            :
            <ToggleButton value="ERP Dashboard" onClick={() => setToggle('ERP Dashboard')}>ERP Dashboard</ToggleButton>
          }
          <Divider />
          {toggle === 'Mobile Responsive' ?
            <ToggleButton active value="Mobile Responsive" onClick={() => setToggle('Mobile Responsive')}>Mobile Responsive</ToggleButton>
            :
            <ToggleButton value="Mobile Responsive" onClick={() => setToggle('Mobile Responsive')}>Mobile Responsive</ToggleButton>
          }
        </ToggleButtonGroup>
        <CardContainer>
          {toggle === 'all' && projects
            .map((project) => (
              <ProjectCard project={project} openModal={openModal} setOpenModal={setOpenModal}/>
            ))}
          {projects
            .filter((item) => item.category === toggle)
            .map((project) => (
              <ProjectCard project={project} openModal={openModal} setOpenModal={setOpenModal}/>
            ))}
        </CardContainer>
      </Wrapper>
    </Container>
  )
}

export default Projects