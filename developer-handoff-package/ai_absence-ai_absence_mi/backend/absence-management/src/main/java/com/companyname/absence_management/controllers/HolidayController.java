package com.companyname.absence_management.controllers;

import com.companyname.absence_management.model.Holiday;
import com.companyname.absence_management.services.HolidayService;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/holidays")
@CrossOrigin(origins="*")
public class HolidayController {
    private final HolidayService service;
    
    public HolidayController(HolidayService service) {
        this.service = service;
    }

    @GetMapping
    public List<Map<String,Object>> list(@RequestParam int year, @RequestParam(defaultValue = "IN") String country) {
        var items = service.listByYear(country, year);
        List<Map<String,Object>> out = new ArrayList<>();
        for (Holiday h: items) {
            Map<String,Object> m = new HashMap<>();
            m.put("date", h.getDate().toString());
            m.put("name", h.getName());
            m.put("countryCode", h.getCountryCode());
            m.put("region", h.getRegion());
            out.add(m);
        }
        return out;
    }
}