"""
Face recognition utility functions for employee verification
"""
import face_recognition
import numpy as np
from PIL import Image
import io
from django.conf import settings
from .models import Employee


def extract_face_encoding(image_path):
    """
    Extract face encoding from an image file path
    
    Args:
        image_path: Path to the image file
        
    Returns:
        numpy array of face encoding or None if no face found
    """
    try:
        # Load image
        image = face_recognition.load_image_file(image_path)
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(image)
        
        if face_encodings:
            # Return the first face encoding found
            return face_encodings[0]
        else:
            return None
            
    except Exception as e:
        print(f"Error extracting face encoding: {str(e)}")
        return None


def extract_face_encoding_from_file(uploaded_file):
    """
    Extract face encoding from an uploaded file object
    
    Args:
        uploaded_file: Django UploadedFile object
        
    Returns:
        numpy array of face encoding or None if no face found
    """
    try:
        # Read the uploaded file
        image = Image.open(uploaded_file)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert PIL Image to numpy array
        image_array = np.array(image)
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(image_array)
        
        if face_encodings:
            return face_encodings[0]
        else:
            return None
            
    except Exception as e:
        print(f"Error extracting face encoding from file: {str(e)}")
        return None


def compare_faces(known_encoding, unknown_encoding, tolerance=0.6):
    """
    Compare two face encodings
    
    Args:
        known_encoding: numpy array of the known face encoding
        unknown_encoding: numpy array of the unknown face encoding
        tolerance: How much distance between faces to consider a match (default 0.6)
        
    Returns:
        dict with 'match' (bool), 'distance' (float), and 'confidence' (float percentage)
    """
    try:
        if known_encoding is None or unknown_encoding is None:
            return {
                'match': False,
                'distance': 1.0,
                'confidence': 0.0
            }
        
        # Calculate face distance
        face_distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
        
        # Check if faces match
        matches = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=tolerance)
        
        # Calculate confidence (inverse of distance, as percentage)
        confidence = max(0, (1 - face_distance) * 100)
        
        return {
            'match': bool(matches[0]),
            'distance': float(face_distance),
            'confidence': float(confidence)
        }
        
    except Exception as e:
        print(f"Error comparing faces: {str(e)}")
        return {
            'match': False,
            'distance': 1.0,
            'confidence': 0.0
        }


def get_match_tolerance(default=0.6):
    """Read face match tolerance from settings if provided"""
    return getattr(settings, 'FACE_MATCH_TOLERANCE', default)


def is_encoding_unique(new_encoding, exclude_employee_id=None, tolerance=None):
    """
    Check that a face encoding is unique across all employees.

    Args:
        new_encoding: numpy array for new face
        exclude_employee_id: optional employee id to exclude from comparison
        tolerance: optional override tolerance

    Returns:
        (is_unique: bool, conflict_employee: Employee | None, distance: float | None)
    """
    if new_encoding is None:
        return True, None, None

    tol = tolerance if tolerance is not None else get_match_tolerance()

    qs = Employee.objects.exclude(face_encoding__isnull=True)
    if exclude_employee_id:
        qs = qs.exclude(pk=exclude_employee_id)

    for emp in qs:
        known = emp.get_face_encoding()
        if known is None:
            continue
        # Use face_distance to compute similarity
        distance = float(face_recognition.face_distance([known], new_encoding)[0])
        match = bool(face_recognition.compare_faces([known], new_encoding, tolerance=tol)[0])
        if match:
            return False, emp, distance

    return True, None, None


def validate_face_image(image_path):
    """
    Validate that an image contains exactly one detectable face
    
    Args:
        image_path: Path to the image file
        
    Returns:
        dict with 'valid' (bool), 'face_count' (int), and 'message' (str)
    """
    try:
        # Load image
        image = face_recognition.load_image_file(image_path)
        
        # Detect faces
        face_locations = face_recognition.face_locations(image)
        face_count = len(face_locations)
        
        if face_count == 0:
            return {
                'valid': False,
                'face_count': 0,
                'message': 'No face detected in the image. Please upload a clear photo of your face.'
            }
        elif face_count > 1:
            return {
                'valid': False,
                'face_count': face_count,
                'message': f'Multiple faces detected ({face_count}). Please upload a photo with only one person.'
            }
        else:
            return {
                'valid': True,
                'face_count': 1,
                'message': 'Face detected successfully.'
            }
            
    except Exception as e:
        return {
            'valid': False,
            'face_count': 0,
            'message': f'Error validating image: {str(e)}'
        }


def process_and_store_face_encoding(employee, image_path):
    """
    Process an image and store the face encoding in the employee model
    
    Args:
        employee: Employee model instance
        image_path: Path to the image file
        
    Returns:
        dict with 'success' (bool) and 'message' (str)
    """
    try:
        # Validate the image
        validation = validate_face_image(image_path)
        
        if not validation['valid']:
            return {
                'success': False,
                'message': validation['message']
            }
        
        # Extract face encoding
        encoding = extract_face_encoding(image_path)
        
        if encoding is None:
            return {
                'success': False,
                'message': 'Failed to extract face encoding from the image.'
            }
        
        # Ensure uniqueness across all employees
        is_unique, conflict_emp, distance = is_encoding_unique(encoding, exclude_employee_id=employee.pk)
        if not is_unique:
            return {
                'success': False,
                'message': f'This face appears to match an existing employee ("{conflict_emp.full_name}"). Please use a unique face image.'
            }

        # Store the encoding
        employee.set_face_encoding(encoding)
        employee.save()

        return {
            'success': True,
            'message': 'Face registered successfully!'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error processing face: {str(e)}'
        }
