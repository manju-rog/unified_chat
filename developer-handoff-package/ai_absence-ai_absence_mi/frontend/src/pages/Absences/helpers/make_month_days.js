// Makes the [1..31] + iso strings for month days
import { useState, useCallback, useMemo } from "react";

export function useDateManagement() {
  const [selectedYear, setSelectedYear] = useState(2025);
  const [selectedMonthIndex, setSelectedMonthIndex] = useState(8); // August (0-based)
  const [isDatePickerOpen, setIsDatePickerOpen] = useState(false);

  // Calculate days in selected month
  const daysInSelectedMonth = useMemo(() => {
    return new Date(selectedYear, selectedMonthIndex + 1, 0).getDate();
  }, [selectedYear, selectedMonthIndex]);

  // Check if date is today
  const isToday = useCallback((date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  }, []);

  // Generate array of day objects
  const days = useMemo(() => {
    const daysArray = [];
    for (let day = 1; day <= daysInSelectedMonth; day++) {
      const date = new Date(selectedYear, selectedMonthIndex, day);
      const dayName = date
        .toLocaleDateString("en-US", { weekday: "short" })
        .toUpperCase();
      // Use timezone-safe date formatting to avoid +1 day issue
      const isoString = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

      daysArray.push({
        day,
        dayName,
        isoString,
        isToday: isToday(date),
      });
    }
    return daysArray;
  }, [selectedYear, selectedMonthIndex, daysInSelectedMonth, isToday]);

  // Check if current month is selected
  const isCurrentMonth = useMemo(() => {
    const today = new Date();
    return (
      selectedYear === today.getFullYear() &&
      selectedMonthIndex === today.getMonth()
    );
  }, [selectedYear, selectedMonthIndex]);

  // Format date for display
  const getFormattedDate = useCallback(() => {
    const monthNames = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];
    return `${monthNames[selectedMonthIndex]} ${selectedYear}`;
  }, [selectedYear, selectedMonthIndex]);

  // Date picker handlers
  const handleOpenDatePicker = useCallback(() => {
    setIsDatePickerOpen(true);
  }, []);

  const handleCloseDatePicker = useCallback(() => {
    setIsDatePickerOpen(false);
  }, []);

  const handleYearChange = useCallback((year) => {
    setSelectedYear(parseInt(year));
  }, []);

  const handleMonthChange = useCallback((monthIndex) => {
    setSelectedMonthIndex(monthIndex);
    setIsDatePickerOpen(false);
  }, []);

  const handlePreviousMonth = useCallback(() => {
    if (selectedMonthIndex === 0) {
      setSelectedYear((prev) => prev - 1);
      setSelectedMonthIndex(11);
    } else {
      setSelectedMonthIndex((prev) => prev - 1);
    }
  }, [selectedMonthIndex]);

  const handleNextMonth = useCallback(() => {
    if (selectedMonthIndex === 11) {
      setSelectedYear((prev) => prev + 1);
      setSelectedMonthIndex(0);
    } else {
      setSelectedMonthIndex((prev) => prev + 1);
    }
  }, [selectedMonthIndex]);

  const handleCurrentMonth = useCallback(() => {
    const today = new Date();
    setSelectedYear(today.getFullYear());
    setSelectedMonthIndex(today.getMonth());
    setIsDatePickerOpen(false);
  }, []);

  // Date picker props object
  const datePickerProps = useMemo(
    () => ({
      selectedYear,
      selectedMonthIndex,
      isDatePickerOpen,
      isCurrentMonth,
      getFormattedDate,
      onOpenDatePicker: handleOpenDatePicker,
      onCloseDatePicker: handleCloseDatePicker,
      onYearChange: handleYearChange,
      onMonthChange: handleMonthChange,
      onPreviousMonth: handlePreviousMonth,
      onNextMonth: handleNextMonth,
      onCurrentMonth: handleCurrentMonth,
    }),
    [
      selectedYear,
      selectedMonthIndex,
      isDatePickerOpen,
      isCurrentMonth,
      getFormattedDate,
      handleOpenDatePicker,
      handleCloseDatePicker,
      handleYearChange,
      handleMonthChange,
      handlePreviousMonth,
      handleNextMonth,
      handleCurrentMonth,
    ]
  );

  return {
    selectedYear,
    selectedMonthIndex,
    isDatePickerOpen,
    daysInSelectedMonth,
    days,
    getFormattedDate,
    isCurrentMonth,
    datePickerProps,
    handleCloseDatePicker,
  };
}
