import supabaseAuthService from './supabaseAuthService';

class FileUploadService {
  constructor() {
    this.bucketName = 'customer-documents';
  }

  // Get the current supabase client with authentication
  getSupabaseClient() {
    return supabaseAuthService.getClient();
  }

  // Upload file to Supabase Storage
  async uploadFile(file, customerId, tenantId) {
    try {
      const supabase = this.getSupabaseClient();
      
      // Check if user is authenticated
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        throw new Error('User not authenticated');
      }

      // Create a unique file name
      const fileExt = file.name.split('.').pop();
      const fileName = `${tenantId}/${customerId}/incorporation_doc_${Date.now()}.${fileExt}`;

      console.log('Uploading file:', fileName, 'to bucket:', this.bucketName);

      // Upload file to Supabase Storage
      const { data, error } = await supabase.storage
        .from(this.bucketName)
        .upload(fileName, file, {
          cacheControl: '3600',
          upsert: false
        });

      if (error) {
        console.error('Supabase storage upload error:', error);
        throw error;
      }

      console.log('File uploaded successfully:', data);

      // Get the public URL
      const { data: { publicUrl } } = supabase.storage
        .from(this.bucketName)
        .getPublicUrl(fileName);

      return {
        success: true,
        path: data.path,
        publicUrl: publicUrl
      };
    } catch (error) {
      console.error('File upload error:', error);
      return {
        success: false,
        error: error.message || 'File upload failed'
      };
    }
  }

  // Download file from Supabase Storage
  async downloadFile(filePath) {
    try {
      const supabase = this.getSupabaseClient();
      
      const { data, error } = await supabase.storage
        .from(this.bucketName)
        .download(filePath);

      if (error) throw error;

      return {
        success: true,
        data: data
      };
    } catch (error) {
      console.error('File download error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Get signed URL for private file access
  async getSignedUrl(filePath, expiresIn = 3600) {
    try {
      const supabase = this.getSupabaseClient();
      
      const { data, error } = await supabase.storage
        .from(this.bucketName)
        .createSignedUrl(filePath, expiresIn);

      if (error) throw error;

      return {
        success: true,
        signedUrl: data.signedUrl
      };
    } catch (error) {
      console.error('Get signed URL error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Delete file from Supabase Storage
  async deleteFile(filePath) {
    try {
      const supabase = this.getSupabaseClient();
      
      const { error } = await supabase.storage
        .from(this.bucketName)
        .remove([filePath]);

      if (error) throw error;

      return {
        success: true
      };
    } catch (error) {
      console.error('File delete error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Validate file type and size
  validateFile(file) {
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'image/jpeg',
      'image/png'
    ];

    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'Invalid file type. Please upload PDF, Word documents, or images (JPEG/PNG).'
      };
    }

    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'File size exceeds 10MB limit.'
      };
    }

    return {
      valid: true
    };
  }
}

export default new FileUploadService();