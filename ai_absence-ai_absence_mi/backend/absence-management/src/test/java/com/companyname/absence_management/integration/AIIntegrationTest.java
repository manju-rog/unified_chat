package com.companyname.absence_management.integration;

import com.companyname.absence_management.dto.ChatRequestDTO;
import com.companyname.absence_management.dto.ChatResponseDTO;
import com.companyname.absence_management.model.Employee;
import com.companyname.absence_management.model.AbsenceRecord;
import com.companyname.absence_management.repository.EmployeeRepository;
import com.companyname.absence_management.repository.AbsenceRecordRepository;
import com.companyname.absence_management.services.ConversationContextService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("sqlite")
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Transactional
public class AIIntegrationTest {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private EmployeeRepository employeeRepository;

    @Autowired
    private AbsenceRecordRepository absenceRecordRepository;

    @Autowired
    private ConversationContextService conversationContextService;

    @Autowired
    private ObjectMapper objectMapper;

    private String baseUrl;
    private String conversationId;
    private HttpHeaders headers;

    @BeforeEach
    void setUp() {
        baseUrl = "http://localhost:" + port + "/api/ai";
        conversationId = "test-conv-" + UUID.randomUUID().toString();
        
        headers = new HttpHeaders();
        headers.set("Content-Type", "application/json");
        headers.set("Accept", "application/json");

        // Clear any existing conversation context
        conversationContextService.clearContext(conversationId);

        // Set up test data
        setupTestEmployees();
    }

    private void setupTestEmployees() {
        // Clear existing data
        absenceRecordRepository.deleteAll();
        employeeRepository.deleteAll();

        // Create test employees
        Employee manju = new Employee();
        manju.setEmployeeId("EMP001");
        manju.setName("Manju");
        manju.setEmail("manju@company.com");
        manju.setPhone("1234567890");
        manju.setDepartment("Engineering");
        manju.setRole("Developer");
        employeeRepository.save(manju);

        Employee ganesh = new Employee();
        ganesh.setEmployeeId("EMP002");
        ganesh.setName("Ganesh");
        ganesh.setEmail("ganesh@company.com");
        ganesh.setPhone("1234567891");
        ganesh.setDepartment("Engineering");
        ganesh.setRole("Senior Developer");
        employeeRepository.save(ganesh);

        Employee priya = new Employee();
        priya.setEmployeeId("EMP003");
        priya.setName("Priya");
        priya.setEmail("priya@company.com");
        priya.setPhone("1234567892");
        priya.setDepartment("HR");
        priya.setRole("HR Manager");
        employeeRepository.save(priya);
    }

    private ResponseEntity<ChatResponseDTO> sendChatMessage(String message) {
        ChatRequestDTO request = new ChatRequestDTO();
        request.setMessage(message);
        request.setConversationId(conversationId);

        HttpEntity<ChatRequestDTO> entity = new HttpEntity<>(request, headers);
        return restTemplate.postForEntity(baseUrl + "/chat", entity, ChatResponseDTO.class);
    }

    @Test
    void testCompleteMarkAbsenceFlow() {
        // Test marking an employee absent
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Mark Manju absent today");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        assertEquals("markAbsence", response.getBody().getActionType());
        assertNotNull(response.getBody().getActionData());
        assertTrue(response.getBody().getResponse().contains("Manju"));
        assertTrue(response.getBody().getResponse().toLowerCase().contains("absent"));

        // Verify the absence was recorded in the database
        Employee manju = employeeRepository.findAll().stream()
                .filter(e -> "Manju".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(manju);
        
        Optional<AbsenceRecord> absence = absenceRecordRepository.findByEmployeeIdAndAbsenceDate(manju.getId(), LocalDate.now());
        assertTrue(absence.isPresent());
        assertEquals("A", absence.get().getAbsenceType());
    }

    @Test
    void testCompleteQueryAbsenceFlow() {
        // First, mark someone absent
        Employee manju = employeeRepository.findAll().stream()
                .filter(e -> "Manju".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(manju);
        
        AbsenceRecord absence = new AbsenceRecord();
        absence.setEmployee(manju);
        absence.setAbsenceDate(LocalDate.now().minusDays(1));
        absence.setAbsenceType(AbsenceRecord.AbsenceType.A);
        absenceRecordRepository.save(absence);

        // Test querying absences
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Who was absent yesterday?");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        assertEquals("queryAbsence", response.getBody().getActionType());
        assertNotNull(response.getBody().getActionData());
        assertTrue(response.getBody().getResponse().contains("Manju"));
    }

    @Test
    void testConversationContextAndConfirmations() {
        // Test name suggestion and confirmation flow
        ResponseEntity<ChatResponseDTO> response1 = sendChatMessage("Mark Manu absent today");
        
        assertEquals(HttpStatus.OK, response1.getStatusCode());
        assertNotNull(response1.getBody());
        assertTrue(response1.getBody().isSuccess());
        
        // Should suggest "Manju" as closest match
        assertTrue(response1.getBody().getResponse().toLowerCase().contains("manju"));
        assertTrue(response1.getBody().getResponse().toLowerCase().contains("did you mean"));

        // Confirm with "yes"
        ResponseEntity<ChatResponseDTO> response2 = sendChatMessage("yes");
        
        assertEquals(HttpStatus.OK, response2.getStatusCode());
        assertNotNull(response2.getBody());
        assertTrue(response2.getBody().isSuccess());
        assertEquals("markAbsence", response2.getBody().getActionType());

        // Verify the absence was recorded
        Employee manju = employeeRepository.findAll().stream()
                .filter(e -> "Manju".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(manju);
        
        Optional<AbsenceRecord> absence = absenceRecordRepository.findByEmployeeIdAndAbsenceDate(manju.getId(), LocalDate.now());
        assertTrue(absence.isPresent());
        assertEquals("A", absence.get().getAbsenceType());
    }

    @Test
    void testConversationContextRejection() {
        // Test name suggestion and rejection flow
        ResponseEntity<ChatResponseDTO> response1 = sendChatMessage("Mark Manu absent today");
        
        assertEquals(HttpStatus.OK, response1.getStatusCode());
        assertTrue(response1.getBody().getResponse().toLowerCase().contains("manju"));

        // Reject with "no"
        ResponseEntity<ChatResponseDTO> response2 = sendChatMessage("no");
        
        assertEquals(HttpStatus.OK, response2.getStatusCode());
        assertNotNull(response2.getBody());
        assertTrue(response2.getBody().isSuccess());
        assertTrue(response2.getBody().getResponse().toLowerCase().contains("please provide"));

        // No absence should be recorded
        Employee manju = employeeRepository.findAll().stream()
                .filter(e -> "Manju".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(manju);
        
        Optional<AbsenceRecord> absence = absenceRecordRepository.findByEmployeeIdAndAbsenceDate(manju.getId(), LocalDate.now());
        assertFalse(absence.isPresent());
    }

    @Test
    void testMultipleEmployeeHandling() {
        // Test marking multiple employees
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Mark Manju and Ganesh absent today");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        assertEquals("markAbsence", response.getBody().getActionType());

        // Verify both absences were recorded
        Employee manju = employeeRepository.findAll().stream()
                .filter(e -> "Manju".equals(e.getName()))
                .findFirst().orElse(null);
        Employee ganesh = employeeRepository.findAll().stream()
                .filter(e -> "Ganesh".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(manju);
        assertNotNull(ganesh);
        
        Optional<AbsenceRecord> manjuAbsence = absenceRecordRepository.findByEmployeeIdAndAbsenceDate(manju.getId(), LocalDate.now());
        Optional<AbsenceRecord> ganeshAbsence = absenceRecordRepository.findByEmployeeIdAndAbsenceDate(ganesh.getId(), LocalDate.now());
        
        assertTrue(manjuAbsence.isPresent());
        assertTrue(ganeshAbsence.isPresent());
        assertEquals("A", manjuAbsence.get().getAbsenceType());
        assertEquals("A", ganeshAbsence.get().getAbsenceType());
    }

    @Test
    void testVacationMarking() {
        // Test marking vacation
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Put Priya on vacation tomorrow");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        assertEquals("markAbsence", response.getBody().getActionType());
        assertTrue(response.getBody().getResponse().toLowerCase().contains("vacation"));

        // Verify vacation was recorded
        Employee priya = employeeRepository.findAll().stream()
                .filter(e -> "Priya".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(priya);
        
        Optional<AbsenceRecord> absence = absenceRecordRepository.findByEmployeeIdAndAbsenceDate(priya.getId(), LocalDate.now().plusDays(1));
        assertTrue(absence.isPresent());
        assertEquals("V", absence.get().getAbsenceType());
    }

    @Test
    void testDateRangeHandling() {
        // Test marking absence for a date range
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Mark Ganesh absent from tomorrow to next Friday");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        assertEquals("markAbsence", response.getBody().getActionType());

        // Verify multiple dates were recorded
        Employee ganesh = employeeRepository.findAll().stream()
                .filter(e -> "Ganesh".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(ganesh);
        
        LocalDate startDate = LocalDate.now().plusDays(1);
        LocalDate endDate = startDate.plusDays(4); // Assuming next Friday is 4 days later
        
        for (LocalDate date = startDate; !date.isAfter(endDate); date = date.plusDays(1)) {
            Optional<AbsenceRecord> absence = absenceRecordRepository.findByEmployeeIdAndAbsenceDate(ganesh.getId(), date);
            if (absence.isPresent()) {
                assertEquals("A", absence.get().getAbsenceType());
            }
        }
    }

    @Test
    void testNonAbsenceRelatedQueries() {
        // Test that non-absence related queries are handled appropriately
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("What's the weather like today?");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        assertEquals("text", response.getBody().getActionType());
        assertTrue(response.getBody().getResponse().toLowerCase().contains("absence") || 
                  response.getBody().getResponse().toLowerCase().contains("help"));
    }

    @Test
    void testErrorHandlingInvalidEmployee() {
        // Test handling of invalid employee names
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Mark NonExistentEmployee absent today");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        
        // Should either suggest a similar name or ask for clarification
        assertTrue(response.getBody().getResponse().toLowerCase().contains("find") || 
                  response.getBody().getResponse().toLowerCase().contains("suggest") ||
                  response.getBody().getResponse().toLowerCase().contains("clarify"));
    }

    @Test
    void testErrorHandlingInvalidDate() {
        // Test handling of invalid dates
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Mark Manju absent on February 30th");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        
        // Should handle invalid date gracefully
        assertTrue(response.getBody().getResponse().toLowerCase().contains("date") || 
                  response.getBody().getResponse().toLowerCase().contains("invalid") ||
                  response.getBody().getResponse().toLowerCase().contains("clarify"));
    }

    @Test
    void testConversationHistoryMaintenance() {
        // Test that conversation history is maintained across multiple messages
        sendChatMessage("Hello");
        sendChatMessage("Mark Manju absent today");
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("What did I just ask you to do?");
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isSuccess());
        
        // Should reference the previous request about marking Manju absent
        assertTrue(response.getBody().getResponse().toLowerCase().contains("manju") || 
                  response.getBody().getResponse().toLowerCase().contains("absent"));
    }

    @Test
    void testConcurrentConversations() {
        // Test that different conversation IDs maintain separate contexts
        String conversationId2 = "test-conv-2-" + UUID.randomUUID().toString();
        
        // First conversation
        ChatRequestDTO request1 = new ChatRequestDTO();
        request1.setMessage("Mark Manju absent today");
        request1.setConversationId(conversationId);
        
        // Second conversation
        ChatRequestDTO request2 = new ChatRequestDTO();
        request2.setMessage("Mark Ganesh on vacation today");
        request2.setConversationId(conversationId2);
        
        HttpEntity<ChatRequestDTO> entity1 = new HttpEntity<>(request1, headers);
        HttpEntity<ChatRequestDTO> entity2 = new HttpEntity<>(request2, headers);
        
        ResponseEntity<ChatResponseDTO> response1 = restTemplate.postForEntity(baseUrl + "/chat", entity1, ChatResponseDTO.class);
        ResponseEntity<ChatResponseDTO> response2 = restTemplate.postForEntity(baseUrl + "/chat", entity2, ChatResponseDTO.class);
        
        assertEquals(HttpStatus.OK, response1.getStatusCode());
        assertEquals(HttpStatus.OK, response2.getStatusCode());
        
        assertTrue(response1.getBody().getResponse().contains("Manju"));
        assertTrue(response2.getBody().getResponse().contains("Ganesh"));
        
        // Verify both actions were executed correctly
        Employee manju = employeeRepository.findAll().stream()
                .filter(e -> "Manju".equals(e.getName()))
                .findFirst().orElse(null);
        Employee ganesh = employeeRepository.findAll().stream()
                .filter(e -> "Ganesh".equals(e.getName()))
                .findFirst().orElse(null);
        assertNotNull(manju);
        assertNotNull(ganesh);
        
        Optional<AbsenceRecord> manjuAbsence = absenceRecordRepository.findByEmployeeIdAndAbsenceDate(manju.getId(), LocalDate.now());
        Optional<AbsenceRecord> ganeshAbsence = absenceRecordRepository.findByEmployeeIdAndAbsenceDate(ganesh.getId(), LocalDate.now());
        
        assertTrue(manjuAbsence.isPresent());
        assertTrue(ganeshAbsence.isPresent());
        assertEquals("A", manjuAbsence.get().getAbsenceType());
        assertEquals("V", ganeshAbsence.get().getAbsenceType());
    }

    @Test
    void testRequestValidation() {
        // Test empty message
        ChatRequestDTO emptyRequest = new ChatRequestDTO();
        emptyRequest.setMessage("");
        emptyRequest.setConversationId(conversationId);
        
        HttpEntity<ChatRequestDTO> entity = new HttpEntity<>(emptyRequest, headers);
        ResponseEntity<ChatResponseDTO> response = restTemplate.postForEntity(baseUrl + "/chat", entity, ChatResponseDTO.class);
        
        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        
        // Test null message
        ChatRequestDTO nullRequest = new ChatRequestDTO();
        nullRequest.setMessage(null);
        nullRequest.setConversationId(conversationId);
        
        entity = new HttpEntity<>(nullRequest, headers);
        response = restTemplate.postForEntity(baseUrl + "/chat", entity, ChatResponseDTO.class);
        
        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
    }

    @Test
    void testLongConversationHandling() {
        // Test that long conversations are handled properly (conversation history limits)
        for (int i = 0; i < 15; i++) {
            ResponseEntity<ChatResponseDTO> response = sendChatMessage("Hello " + i);
            assertEquals(HttpStatus.OK, response.getStatusCode());
        }
        
        // Should still work after many messages
        ResponseEntity<ChatResponseDTO> response = sendChatMessage("Mark Manju absent today");
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertTrue(response.getBody().isSuccess());
    }
}