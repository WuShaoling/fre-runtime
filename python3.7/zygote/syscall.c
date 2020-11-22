#include <Python.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <stdio.h>
#include <sched.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/types.h>
#include <sys/wait.h>

static PyObject *syscall_unshare(PyObject *module) {
    int res = unshare(CLONE_NEWUTS | CLONE_NEWPID | CLONE_NEWIPC | CLONE_NEWNS);
    return Py_BuildValue("i", res);
}

static PyObject *syscall_fork(PyObject *module) {
    int res = fork();
    return Py_BuildValue("i", res);
}

static PyMethodDef pyMethods[] = {
    {"unshare", (PyCFunction)syscall_unshare, METH_NOARGS, "unshare"},
    {"fork", (PyCFunction)syscall_fork, METH_NOARGS, "fork"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef pyModuleDef = {
    PyModuleDef_HEAD_INIT,
    "syscall",
    NULL,
    -1,
    pyMethods
};

PyMODINIT_FUNC PyInit_syscall(void) {
    return PyModule_Create(&pyModuleDef);
}
