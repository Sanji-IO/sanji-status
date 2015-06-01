# -*- coding: utf-8 -*-

import unittest

import os
from datetime import datetime

from contextlib import closing

from sanji_status.dao import Database


class TestDao(unittest.TestCase):
    def setUp(self):
        self.dbpath = os.path.join('/', 'dev', 'shm', 'sanji-status.tests.test_dao.sqlite3')
        try:
            os.unlink(self.dbpath)
        except:
            pass

        self.database = Database(self.dbpath)
        self.database.create_tables_if_needed()

    def tearDown(self):
        try:
            os.unlink(self.dbpath)
        except:
            pass

    def test_CreateTablesIfNeeded_WhenTablesCreated_ShouldPass(self):
        # arrange

        # act
        self.database.create_tables_if_needed()

        # nothing to assert

    def test_InsertReading_ShouldPass(self):
        # arrange

        # act
        self.database.insert_reading(
            12.5,
            400000,
            10000000,
            datetime(2015, 5, 27)
        )

        # assert
        with closing(self.database._connect()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT cpu_usage_percent, mem_usage_byte, disk_usage_byte'
                ' FROM readings;'
            )

            rows = cursor.fetchall()

        self.assertEqual(len(rows), 1)

        cpu_usage_percent, mem_usage_byte, disk_usage_byte = rows[0]
        self.assertEqual(cpu_usage_percent, 12.5)
        self.assertEqual(mem_usage_byte, 400000)
        self.assertEqual(disk_usage_byte, 10000000)

    def test_DeleteOldReadings_ShouldPass(self):
        # arrange
        reading_list = [
            (1, 1, 1, datetime(2015, 5, 1)),
            (2, 2, 2, datetime(2015, 5, 2)),
            (3, 3, 3, datetime(2015, 5, 3)),
            (4, 4, 4, datetime(2015, 5, 4)),
            (5, 5, 5, datetime(2015, 5, 5)),
        ]

        for reading in reading_list:
            self.database.insert_reading(*reading)

        # act
        self.database.delete_old_readings(1)

        # assert
        with closing(self.database._connect()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT cpu_usage_percent, mem_usage_byte, disk_usage_byte'
                ' FROM readings;'
            )

            rows = cursor.fetchall()

        self.assertEqual(len(rows), 1)
        cpu_usage_percent, mem_usage_byte, disk_usage_byte = rows[0]
        self.assertEqual(cpu_usage_percent, 5)
        self.assertEqual(mem_usage_byte, 5)
        self.assertEqual(disk_usage_byte, 5)

    def test_GetLatestReadings_ShouldPass(self):
        # arrange
        reading_list = [
            (1, 1, 1, datetime(2015, 5, 1)),
            (2, 2, 2, datetime(2015, 5, 2)),
            (3, 3, 3, datetime(2015, 5, 3)),
            (4, 4, 4, datetime(2015, 5, 4)),
            (5, 5, 5, datetime(2015, 5, 5)),
        ]

        for reading in reading_list:
            self.database.insert_reading(*reading)

        # act
        result_list = self.database.get_latest_readings(3)

        # assert
        self.assertEqual(
            result_list,
            [
                (datetime(2015, 5, 5), 5, 5, 5),
                (datetime(2015, 5, 4), 4, 4, 4),
                (datetime(2015, 5, 3), 3, 3, 3),
            ]
        )

    def test_Vacuum_ShouldPass(self):
        # arrange

        # act
        self.database.vacuum()

        # nothing to assert
