"""Service for loading and querying course items from JSON data."""

from dataclasses import dataclass

import json
import operator
from typing import List, Optional, final

from pydantic import TypeAdapter
from app.models.order import Order, PostOrder, PreOrder
from app.settings import settings
from app.models.item import Item, Course, Lab, Task, Step

# ===
# This module demonstrates the basics of functional programming.
# ===


def find_by_id[T: Item](items: List[T], item_id: str) -> Optional[T]:
    """
    Searches a list of items for a specific ID.
    Returns the item if found, otherwise None.
    """
    for item in items:
        if item.id == item_id:
            return item
    return None


def get_course_by_id(courses: List[Course], course_id: str) -> Optional[Course]:
    return find_by_id(items=courses, item_id=course_id)


def get_lab_by_id(course: Course, lab_id: str) -> Optional[Lab]:
    return find_by_id(items=course.labs, item_id=lab_id)


def get_task_by_id(lab: Lab, task_id: str) -> Optional[Task]:
    return find_by_id(items=lab.tasks, item_id=task_id)


def get_step_by_id(task: Task, step_id: str) -> Optional[Step]:
    return find_by_id(items=task.steps, item_id=step_id)


def get_course_by_path(courses: List[Course], course_id: str) -> Optional[Course]:
    return get_course_by_id(courses=courses, course_id=course_id)


def get_lab_by_path(
    courses: List[Course], course_id: str, lab_id: str
) -> Optional[Lab]:
    course = get_course_by_path(courses=courses, course_id=course_id)
    if course is not None:
        return get_lab_by_id(course=course, lab_id=lab_id)
    return None


def get_task_by_path(
    courses: List[Course], course_id: str, lab_id: str, task_id: str
) -> Optional[Task]:
    lab = get_lab_by_path(courses=courses, course_id=course_id, lab_id=lab_id)
    if lab is not None:
        return get_task_by_id(lab=lab, task_id=task_id)
    return None


def get_step_by_path(
    courses: List[Course], course_id: str, lab_id: str, task_id: str, step_id: str
) -> Optional[Step]:
    task = get_task_by_path(
        courses=courses, course_id=course_id, lab_id=lab_id, task_id=task_id
    )
    if task is not None:
        return get_step_by_id(task=task, step_id=step_id)
    return None


@final
@dataclass
class FoundItem:
    """
    Helper type for search results
    """

    item: Item
    visited_nodes: int


def get_item_by_id_dfs_iterative(
    courses: List[Course], item_id: str, order: Order
) -> Optional[FoundItem]:
    """Find an item by its id using DFS."""
    counter = 0
    match order:
        case PreOrder():
            for course in courses:
                counter += 1
                if course.id == item_id:
                    return FoundItem(course, counter)

                for lab in course.labs:
                    counter += 1
                    if lab.id == item_id:
                        return FoundItem(lab, counter)

                    for task in lab.tasks:
                        counter += 1
                        if task.id == item_id:
                            return FoundItem(task, counter)

                        for step in task.steps:
                            counter += 1
                            if step.id == item_id:
                                return FoundItem(step, counter)
        case PostOrder():
            # TODO implement
            pass
    return None


def get_item_by_id_dfs_recursive[T: Item](
    items: List[T], item_id: str, order: Order
) -> Optional[FoundItem]:
    visited_nodes: int = 0

    def get_item_by_id_dfs_recursive_[P: Item](
        items: List[P], item_id: str, order: Order
    ) -> Optional[FoundItem]:
        nonlocal visited_nodes

        for item in items:
            match order:
                case PreOrder():
                    visited_nodes += 1
                    if item.id == item_id:
                        return FoundItem(item=item, visited_nodes=visited_nodes)
                case _:
                    pass

            @operator.call
            def go_items() -> Optional[FoundItem]:
                def go[S: Item](items: List[S]):
                    return get_item_by_id_dfs_recursive_(
                        items=items,
                        item_id=item_id,
                        order=order,
                    )

                match item:
                    case Course():
                        return go(items=item.labs)
                    case Lab():
                        return go(items=item.tasks)
                    case Task():
                        return go(items=item.steps)
                    case Step():
                        return

            if go_items is not None:
                return go_items

            match order:
                case PostOrder():
                    visited_nodes += 1
                    if item.id == item_id:
                        return FoundItem(item=item, visited_nodes=visited_nodes)
                case _:
                    pass
        return None

    return get_item_by_id_dfs_recursive_(items=items, item_id=item_id, order=order)


CoursesAdapter = TypeAdapter(type=List[Course])


def read_courses() -> List[Course]:
    with open(settings.course_items_path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    return CoursesAdapter.validate_python(raw)


def get_item_by_id(item_id: str, order: Order) -> Optional[FoundItem]:
    courses: list[Course] = read_courses()
    return get_item_by_id_dfs_iterative(courses=courses, item_id=item_id, order=order)
